#!/usr/bin/env python3
"""Limited feedback checker for the single published lineage scene.

This checks public geometry, native-link structure, and document structure.
The evaluator uses a separate protected implementation and a wider scene family.
"""

import argparse
import json
from pathlib import Path
import traceback
import zipfile

import FreeCAD as App
import Part


TOL = 1.0e-7


def close_number(left, right):
    return abs(float(left) - float(right)) <= TOL * max(1.0, abs(float(right)))


def nonzero_faces(shape):
    if shape is None or shape.isNull():
        return []
    return [face for face in shape.Faces if face.Area > TOL]


def overlap_area(left, right):
    return sum(face.common(other).Area for face in left for other in right)


def positive_overlap(faces):
    return any(faces[i].common(faces[j]).Area > TOL
               for i in range(len(faces)) for j in range(i + 1, len(faces)))


def coverage(actual, target):
    actual_area = sum(face.Area for face in actual)
    target_area = sum(face.Area for face in target)
    common_area = overlap_area(actual, target)
    return (close_number(actual_area, target_area)
            and close_number(common_area, actual_area)
            and close_number(common_area, target_area)
            and not positive_overlap(actual)
            and not positive_overlap(target))


def transformed(shape, placement):
    value = shape.copy()
    value.Placement = placement.multiply(value.Placement)
    return value


def to_local(shape, frame):
    return transformed(shape, frame.inverse())


def to_world(shape, frame):
    return transformed(shape, frame)


def all_vertices_at(face, axis, value):
    return bool(face.Vertexes) and all(
        abs(getattr(vertex.Point, axis) - value) <= TOL
        for vertex in face.Vertexes)


def local_tool_faces(world_tool, surface_frame):
    tool = to_local(world_tool, surface_frame)
    box = tool.BoundBox
    tests = (
        ("X_MIN", "x", box.XMin), ("X_MAX", "x", box.XMax),
        ("Y_MIN", "y", box.YMin), ("Y_MAX", "y", box.YMax),
        ("Z_MIN", "z", box.ZMin), ("Z_MAX", "z", box.ZMax),
    )
    result = {}
    for name, axis, coordinate in tests:
        matches = [face for face in tool.Faces
                   if all_vertices_at(face, axis, coordinate)]
        if len(matches) != 1:
            raise AssertionError("public tool is outside the box contract")
        result[name] = matches[0]
    return result


def parse_edit(path):
    payload = json.loads(Path(path).read_text())
    if payload == {}:
        return {}
    if set(payload) != {"REPEAT_CUT"}:
        raise AssertionError("edit must contain only REPEAT_CUT")
    row = payload["REPEAT_CUT"]
    if set(row) != {"X0", "XLength", "Y0", "YLength"}:
        raise AssertionError("invalid REPEAT_CUT fields")
    result = {key: float(value) for key, value in row.items()}
    if result["XLength"] <= 0 or result["YLength"] <= 0:
        raise AssertionError("edit lengths must be positive")
    return result


def effective_edit(edit_path, prior_edit_path):
    value = {}
    for path in (prior_edit_path, edit_path):
        if path:
            row = parse_edit(path)
            if row:
                value = row
    return value


def make_repeat(pristine, edit, frame):
    operation = next(obj for obj in pristine.OperationGraph.Operations
                     if str(obj.OperationId) == "REPEAT_CUT")
    original = to_local(operation.Tool.Shape, frame)
    if not edit:
        return original
    box = original.BoundBox
    return Part.makeBox(
        edit["XLength"], edit["YLength"], box.ZMax - box.ZMin,
        App.Vector(edit["X0"], edit["Y0"], box.ZMin))


def refined(shape):
    value = shape.removeSplitter()
    if value.isNull() or not value.isValid():
        raise AssertionError("public Boolean produced an invalid shape")
    return value


def build_public_geometry(pristine, edit):
    graph = pristine.OperationGraph
    frame = graph.LocalFrame
    operations = sorted(graph.Operations, key=lambda obj: int(obj.Sequence))
    current = to_local(operations[0].InputStage.Shape, frame)
    shapes = {operations[0].InputStage.Name: current}
    tools = {}
    for operation in operations:
        tool = (make_repeat(pristine, edit, frame)
                if str(operation.OperationId) == "REPEAT_CUT"
                else to_local(operation.Tool.Shape, frame))
        tools[str(operation.OperationId)] = tool
        current = refined(current.cut(tool) if str(operation.Kind).lower() == "cut"
                          else current.fuse(tool))
        shapes[operation.OutputStage.Name] = current
    shapes[graph.Result.Name] = current.copy()
    return frame, shapes, tools


def decode_roles(entries):
    result = {}
    for entry in entries:
        name, values = str(entry).split("=", 1)
        result[name] = tuple(value for value in values.split(",") if value)
    return result


def exposed_regions(surface, final_shape):
    return [piece for boundary in final_shape.Faces
            for piece in nonzero_faces(surface.common(boundary))]


def remove_boundary_regions(faces, earlier_shape):
    result = list(faces)
    for boundary in earlier_shape.Faces:
        next_result = []
        for face in result:
            next_result.extend(nonzero_faces(face.cut(boundary)))
        result = next_result
    return result


def public_regions(pristine, final_local, shapes, tools, edit, frame):
    atlas = []
    pressure = []
    for seed in pristine.OperationGraph.SeedPatches:
        pieces = exposed_regions(to_local(seed.Shape, frame), final_local)
        atlas.extend(pieces)
        if str(seed.SemanticRole) == "PRESSURE":
            pressure.extend(pieces)

    by_role = {"COAT": [], "CONTACT_MASTER": [], "CONTACT_SLAVE": []}
    for operation in pristine.OperationGraph.Operations:
        op_id = str(operation.OperationId)
        if op_id not in {"PRIMARY_CUT", "REPEAT_CUT"}:
            continue
        if op_id == "REPEAT_CUT" and not edit:
            continue
        role_map = decode_roles(operation.SurfaceRoleMap)
        world_tool = to_world(tools[op_id], frame)
        surface_frame = operation.SurfaceFrame
        named_supports = local_tool_faces(world_tool, surface_frame)
        for local_name, surface_local_support in named_supports.items():
            support = to_local(
                to_world(surface_local_support, surface_frame), frame)
            pieces = remove_boundary_regions(
                exposed_regions(support, final_local),
                shapes[operation.InputStage.Name])
            atlas.extend(pieces)
            for role in role_map.get(local_name, ()):
                if role in by_role:
                    by_role[role].extend(pieces)
    return atlas, pressure, by_role


def same_shape(actual, target):
    if actual.isNull() or target.isNull():
        return actual.isNull() and target.isNull()
    try:
        left = actual.cut(target).Volume
        right = target.cut(actual).Volume
    except Exception:
        return False
    return (actual.isValid() and actual.ShapeType == target.ShapeType
            and close_number(actual.Volume, target.Volume)
            and close_number(actual.Area, target.Area)
            and close_number(left, 0.0) and close_number(right, 0.0)
            and len(actual.Faces) == len(target.Faces)
            and len(actual.Edges) == len(target.Edges)
            and len(actual.Vertexes) == len(target.Vertexes))


def property_schema(obj):
    return [(name, obj.getTypeIdOfProperty(name), obj.getGroupOfProperty(name))
            for name in obj.PropertiesList]


def document_structure(pristine, output):
    before = [(obj.Name, int(obj.ID), obj.TypeId, property_schema(obj))
              for obj in pristine.Objects]
    after = [(obj.Name, int(obj.ID), obj.TypeId, property_schema(obj))
             for obj in output.Objects]
    return before == after


def flat_atlas(output):
    obj = output.getObject("LineageFaces")
    shape = obj.Shape
    return (obj.TypeId == "Part::Feature" and shape.ShapeType == "Compound"
            and len(shape.Faces) > 0
            and all(child.ShapeType == "Face" for child in shape.childShapes()))


def linked_faces(output, object_name, property_name):
    atlas = output.getObject("LineageFaces")
    result = []
    for target, names in getattr(output.getObject(object_name), property_name):
        if target is not atlas:
            raise AssertionError("consumer target is not LineageFaces")
        for name in names:
            if not str(name).startswith("Face"):
                raise AssertionError("consumer link is not a Face subelement")
            result.append(atlas.Shape.getElement(str(name)))
    return result


def preflight(path):
    with zipfile.ZipFile(path, "r") as archive:
        names = archive.namelist()
        return ("Document.xml" in names and len(names) == len(set(names))
                and all(not name.startswith(("/", "\\"))
                        and ".." not in Path(name.replace("\\", "/")).parts
                        for name in names))


def verify(args):
    if not preflight(args.output):
        raise AssertionError("unsafe or malformed FCStd archive")
    pristine = App.openDocument(args.pristine)
    output = App.openDocument(args.output)
    baseline = App.openDocument(args.noop_baseline) if args.noop_baseline else None
    try:
        edit = effective_edit(args.edit, args.prior_edit)
        frame, shapes, tools = build_public_geometry(pristine, edit)
        final_local = shapes[pristine.OperationGraph.Result.Name]
        final_world = to_world(final_local, frame)
        target_atlas, target_pressure, roles = public_regions(
            pristine, final_local, shapes, tools, edit, frame)
        atlas_faces = list(output.LineageFaces.Shape.Faces)
        pressure = linked_faces(output, "PressureLoad", "Targets")
        coat = linked_faces(output, "CoatingGroup", "Targets")
        master = linked_faces(output, "ContactPair", "MasterFaces")
        slave = linked_faces(output, "ContactPair", "SlaveFaces")
        checks = {
            "document_structure": document_structure(pristine, output),
            "flat_native_atlas": flat_atlas(output),
            "final_geometry": same_shape(output.FinalSolid.Shape, final_world),
            "result_geometry": same_shape(output.Result.Shape, final_world),
            "atlas_public_regions": coverage(atlas_faces,
                                              [to_world(face, frame) for face in target_atlas]),
            "pressure_public_regions": coverage(pressure,
                                                 [to_world(face, frame) for face in target_pressure]),
            "coat_public_regions": coverage(coat,
                                             [to_world(face, frame) for face in roles["COAT"]]),
            "master_public_regions": coverage(master,
                                               [to_world(face, frame) for face in roles["CONTACT_MASTER"]]),
            "slave_public_regions": coverage(slave,
                                              [to_world(face, frame) for face in roles["CONTACT_SLAVE"]]),
            "master_slave_disjoint": overlap_area(master, slave) <= TOL,
        }
        if args.phase == "repair":
            checks["repair_preserves_saved_final"] = same_shape(
                output.FinalSolid.Shape, pristine.FinalSolid.Shape)
        if args.phase == "noop":
            checks["noop_baseline_present"] = baseline is not None
            if baseline is not None:
                checks["noop_preserves_final"] = same_shape(
                    output.FinalSolid.Shape, baseline.FinalSolid.Shape)
                checks["noop_preserves_atlas"] = coverage(
                    atlas_faces, list(baseline.LineageFaces.Shape.Faces))
        failed = [name for name, passed in checks.items() if not passed]
        return {"status": "accepted" if not failed else "rejected",
                "accepted": not failed, "phase": args.phase,
                "failed_checks": failed, "checks": checks,
                "scope": "single-public-scene-limited-feedback"}
    finally:
        for doc in (baseline, output, pristine):
            if doc is not None:
                App.closeDocument(doc.Name)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pristine", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--edit", required=True)
    parser.add_argument("--prior-edit")
    parser.add_argument("--noop-baseline")
    parser.add_argument("--phase", choices=("repair", "update", "noop"), required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    try:
        report = verify(args)
    except Exception as error:
        report = {"status": "rejected", "accepted": False, "phase": args.phase,
                  "failed_checks": ["checker_exception"], "error": str(error),
                  "traceback": traceback.format_exc(),
                  "scope": "single-public-scene-limited-feedback"}
    Path(args.report).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": report["status"],
                      "failed_checks": report["failed_checks"]}, sort_keys=True))
    raise SystemExit(0 if report["accepted"] else 1)


if __name__ == "__main__":
    main()
