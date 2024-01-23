from compas.geometry import Polygon, Translation, Frame, Transformation
from compas_model.elements import Plate
from compas_model.model import Model
from compas_model.viewer import ViewerModel

# --------------------------------------------------------------------------
# Create a plate from polygon and thickness.
# --------------------------------------------------------------------------
polygon0 = Polygon.from_sides_and_radius_xy(6, 5)

polygon0 = Polygon(points=[
    [0, 0, 0],
    [5, 0, 0],
    [5, 5, 0],
    [10, 5, 0],
    [10, 15, 0],
    [0, 10, 0],

])

# Uncomment to verify the plate is initialized correctly regardless of the polygon winding.
# polygon0.points.reverse()
plate = Plate(polygon=polygon0, thickness=1, compute_loft=False)

# --------------------------------------------------------------------------
# Create a plate from two polygons.
# --------------------------------------------------------------------------
plate = Plate.from_two_polygons(polygon0, polygon0.transformed(Translation.from_vector([0, 0.2, 0.2])))

# --------------------------------------------------------------------------
# Transform and copy the plate.
# --------------------------------------------------------------------------
xform = Transformation.from_frame_to_frame(
    Frame.worldXY(), Frame([0, 0, 0], [1, 0, 0], [0, 1, 0.5])
)
plate.transform(xform)
plate = plate.copy()

# --------------------------------------------------------------------------
# Serialization
# --------------------------------------------------------------------------
plate.to_json("data/plate.json", pretty=True)
plate = Plate.from_json("data/plate.json")

# --------------------------------------------------------------------------
# Create model.
# --------------------------------------------------------------------------
model = Model()
model.add_element("my_plate", plate)
print("Beam plate belongs to the following ElementNode: ",  plate.node)

# --------------------------------------------------------------------------
# Vizualize model.
# --------------------------------------------------------------------------
ViewerModel.show(model, scale_factor=1)
