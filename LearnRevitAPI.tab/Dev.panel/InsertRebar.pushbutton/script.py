# -*- coding: utf-8 -*-
__title__ = "Manual Rebar Placement (SNI)"
__doc__ = """Version = 1.0
Date    = 19.04.2025
_____________________________________________________________________
Description:
1. Select structural elements first
2. Input vertical and horizontal rebar counts (e.g., "3 5")
3. Places rebars according to SNI standards
_____________________________________________________________________
Author: Erik Frits"""

# ╦╔╦╗╔═╗╔═╗╦═╗╔╦╗╔═╗
# ║║║║╠═╝║ ║╠╦╝ ║ ╚═╗
# ╩╩ ╩╩  ╚═╝╩╚═ ╩ ╚═╝ IMPORTS
# ==================================================
import clr

clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
clr.AddReference('RevitServices')

from Autodesk.Revit.DB import *
from Autodesk.Revit.DB.Structure import *
from System.Collections.Generic import List
from pyrevit import revit, forms

# ╦  ╦╔═╗╦═╗╦╔═╗╔╗ ╦  ╔═╗╔═╗
# ╚╗╔╝╠═╣╠╦╝║╠═╣╠╩╗║  ║╣ ╚═╗
#  ╚╝ ╩ ╩╩╚═╩╩ ╩╚═╝╩═╝╚═╝╚═╝ VARIABLES
# ==================================================
doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument

# SNI PARAMETERS
SNI_COVER = 0.040  # 40mm cover


# ╔╦╗╔═╗╦╔╗╔
# ║║║╠═╣║║║║
# ╩ ╩╩ ╩╩╝╚╝ MAIN
# ==================================================
def get_valid_elements():
    """Get user-selected elements that can host rebar"""
    selection = uidoc.Selection.GetElementIds()
    valid_elements = []

    for elem_id in selection:
        element = doc.GetElement(elem_id)
        if not element:
            continue

        # Check if element can host rebar
        if isinstance(element, (FamilyInstance, Wall, Floor)):
            if hasattr(element, 'WallType') and element.WallType.Kind != WallKind.Basic:
                continue
            valid_elements.append(element)

    if not valid_elements:
        forms.alert("No valid structural elements selected!", exitscript=True)
    return valid_elements


def get_rebar_counts():
    """Get vertical and horizontal rebar counts from user"""
    default = "2 2"  # Default: 2 vertical, 2 horizontal
    input = forms.ask_for_string(
        default=default,
        prompt="Enter vertical and horizontal rebar counts (e.g., '3 5')",
        title="Rebar Quantity"
    )

    if not input:
        forms.alert("No input provided!", exitscript=True)

    try:
        parts = input.strip().split()
        vertical = int(parts[0])
        horizontal = int(parts[1]) if len(parts) > 1 else vertical
        return max(1, vertical), max(1, horizontal)  # Minimum 1 rebar
    except:
        forms.alert("Invalid input! Use format '3' or '3 5'", exitscript=True)


def place_rebars(element, rebar_type, vertical, horizontal):
    """Place rebars in element with specified quantities"""
    try:
        bbox = element.get_BoundingBox(None)
        if not bbox:
            print("Skipping {0} - no bounding box".format(element.Id))
            return False

        # Calculate spacing
        width = bbox.Max.X - bbox.Min.X
        height = bbox.Max.Z - bbox.Min.Z

        # Vertical rebars (along height)
        v_spacing = (width - 2 * SNI_COVER) / max(1, (vertical - 1)) if vertical > 1 else 0

        # Horizontal rebars (along width)
        h_spacing = (height - 2 * SNI_COVER) / max(1, (horizontal - 1)) if horizontal > 1 else 0

        # Create rebars
        with Transaction(doc, "Place Rebars") as t:
            t.Start()

            # Vertical rebars
            for i in range(vertical):
                x = bbox.Min.X + SNI_COVER + i * v_spacing
                line = Line.CreateBound(
                    XYZ(x, bbox.Min.Y + SNI_COVER, bbox.Min.Z + SNI_COVER),
                    XYZ(x, bbox.Min.Y + SNI_COVER, bbox.Max.Z - SNI_COVER)
                )
                Rebar.CreateFromCurves(
                    doc, RebarStyle.Standard, rebar_type,
                    None, None, element, XYZ.BasisX, [line],
                    RebarHookOrientation.Right, RebarHookOrientation.Right,
                    True, True
                )

            # Horizontal rebars
            for i in range(horizontal):
                z = bbox.Min.Z + SNI_COVER + i * h_spacing
                line = Line.CreateBound(
                    XYZ(bbox.Min.X + SNI_COVER, bbox.Min.Y + SNI_COVER, z),
                    XYZ(bbox.Max.X - SNI_COVER, bbox.Min.Y + SNI_COVER, z)
                )
                Rebar.CreateFromCurves(
                    doc, RebarStyle.Standard, rebar_type,
                    None, None, element, XYZ.BasisZ, [line],
                    RebarHookOrientation.Right, RebarHookOrientation.Right,
                    True, True
                )

            t.Commit()
        return True

    except Exception as e:
        print("Failed on {0}: {1}".format(element.Id, str(e)))
        return False


# Main execution
if __name__ == '__main__':
    # 1. Let user select elements
    elements = get_valid_elements()

    # 2. Select rebar type
    rebar_types = FilteredElementCollector(doc).OfClass(RebarBarType).ToElements()
    rebar_type_names = []
    for rt in rebar_types:
        param = rt.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM)
        rebar_type_names.append(param.AsString() if param else "Unknown")

    rebar_type_name = forms.SelectFromList.show(
        rebar_type_names,
        title="Select Rebar Type",
        button_name='Select'
    )
    if not rebar_type_name:
        forms.alert("No rebar type selected!", exitscript=True)

    selected_type = None
    for i, name in enumerate(rebar_type_names):
        if name == rebar_type_name:
            selected_type = rebar_types[i]
            break

    if not selected_type:
        forms.alert("Failed to find selected rebar type!", exitscript=True)

    # 3. Get rebar counts
    vertical, horizontal = get_rebar_counts()

    # 4. Execute placement
    success_count = 0
    for element in elements:
        if place_rebars(element, selected_type, vertical, horizontal):
            success_count += 1

    # 5. Show results
    forms.alert(
        "Successfully placed rebar in {0}/{1} elements\n"
        "Vertical: {2} bars\n"
        "Horizontal: {3} bars".format(
            success_count,
            len(elements),
            vertical,
            horizontal
        ),
        title="Rebar Placement Complete"
    )