from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

from compas.geometry import Frame
from compas.geometry import Point
from compas.geometry import Polygon
from compas.geometry import Box
from compas.geometry import convex_hull
from compas.datastructures import Mesh
from compas_model.elements.element import Element


class Block(Element):
    """A block represented by a central point and a mesh.

    The implementation is inspired by the compas_assembly block class:
    https://github.com/BlockResearchGroup/compas_assembly/blob/main/src/compas_assembly/datastructures/block.py

    Parameters
    ----------
    name : str, optional
        Name of the element
    frame : :class:`compas.geometry.Frame`, optional
        Local coordinate of the object, default is :class:`compas.geometry.Frame.WorldXY()`.
    geometry_simplified : Any, optional
        Minimal geometrical represetation of an object. For example a list of :class:`compas.geometry.Polyline` can represent a plate.
    geometry : Any, optional
        A list of closed shapes. For example a box of a beam, a mesh of a block and etc.
    kwargs (dict, optional):
        Additional keyword arguments.

    Attributes
    ----------
    dtype : str, read-only
        The type of the object in the form of a fully qualified module name and a class name, separated by a forward slash ("/").
        For example: ``"compas.datastructures/Mesh"``.
    data : dict
        The representation of the object as a dictionary containing only built-in Python data types.
        The structure of the dict is described by the data schema.
    guid : str, read-only
        The globally unique identifier of the object.
        The guid is generated with ``uuid.uuid4()``.
    name : str
        The name of the object.
        This name is not necessarily unique and can be set by the user.
        The default value is the object's class name: ``self.__class__.__name__``.
    frame : :class:`compas.geometry.Frame`
        Local coordinate of the object, default is :class:`compas.geometry.Frame.WorldXY()`.
    geometry_simplified : :class:`compas.geometry.Line`
        Minimal geometrical represetation of an object. For example a :class:`compas.geometry.Polyline` that can represent: a point, a line or a polyline.
    geometry : :class:`compas.geometry.Box`
        A list of closed shapes. For example a box of a beam, a mesh of a block and etc.
    aabb : :class:`compas.geometry.Box`
        The Axis Aligned Bounding Box (AABB) of the element.
    obb : :class:`compas.geometry.Box`
        The Oriented Bounding Box (OBB) of the element.
    collision_mesh : :class:`compas.datastructures.Mesh`
        The collision geometry of the element.
    dimensions : list
        The dimensions of the element.
    features : dict
        The features of the element, joinery, openings, etc.
    insertion : :class:`compas.geometry.Vector`
        The insertion vector of the element. Default is (0, 0, -1).
    node : :class:`compas_model.model.ElementNode`
        The node of the element.
    face_polygons : list
        Flat area list of the face polygons of the element, used for interface detection.

    """

    def __init__(self, closed_mesh, geometry_simplified=None, **kwargs):

        if not isinstance(closed_mesh, Mesh):
            raise TypeError("Mesh is not of type compas.datastructures.Mesh")

        centroid = Point(*closed_mesh.centroid())
        geometry_simplified = geometry_simplified if geometry_simplified is not None else centroid

        super(Block, self).__init__(
            frame=Frame(centroid, [1, 0, 0], [0, 1, 0]),
            geometry_simplified=geometry_simplified,
            geometry=closed_mesh,
            index=None,
            **kwargs,
        )

        self._face_polygons = []

    # ==========================================================================
    # Serialization.
    # ==========================================================================

    @property
    def data(self):
        return {
            "name": self.name,
            "frame": self.frame,
            "geometry_simplified": self.geometry_simplified,
            "geometry": self.geometry,
            "aabb": self.aabb,
            "obb": self.obb,
            "collision_mesh": self.collision_mesh,
            "dimensions": self.dimensions,
            "features": self.features,
            "insertion": self.insertion,
            "face_polygons": self.face_polygons,
        }

    @classmethod
    def from_data(cls, data):
        element = cls(data["geometry"], data["geometry_simplified"])
        element._name = data["name"]
        element._frame = data["frame"]
        element._aabb = data["aabb"]
        element._obb = data["obb"]
        element._collision_mesh = data["collision_mesh"]
        element._dimensions = data["dimensions"]
        element._features = data["features"]
        element._insertion = data["insertion"]
        element._face_polygons = data["face_polygons"]
        return element

    # ==========================================================================
    # Templated methods to provide minimal information for:
    # aabb
    # obb
    # geometry_collision
    # transform
    # ==========================================================================

    @property
    def dimensions(self):
        if not type(self.geometry) is None:
            self.compute_aabb()
        return [self.aabb.width, self.aabb.height, self.aabb.depth]

    def compute_aabb(self, inflate=0.0):

        """Computes the Axis Aligned Bounding Box (AABB) of the element.

        Attributes
        ----------
        inflate : float
            Offset of box to avoid floating point errors.

        Returns
        -------
        :class:`compas.geometry.Box`
            The AABB of the element.

        """
        self._aabb = Box.from_points(self.geometry.aabb())
        self._aabb.xsize += inflate
        self._aabb.ysize += inflate
        self._aabb.zsize += inflate
        return self._aabb

    def compute_obb(self, inflate=0.0):
        """Computes the Oriented Bounding Box (OBB) of the element.

        Attributes
        ----------
        inflate : float
            Offset of box to avoid floating point errors.

        Returns
        -------
        :class:`compas.geometry.Box`
            The OBB of the element.

        """
        self._obb = Box.from_points(self.geometry.obb())

        self._obb.xsize += inflate
        self._obb.ysize += inflate
        self._obb.zsize += inflate
        return self._obb

    def compute_collision_mesh(self):
        """Computes the collision geometry of the element.

        Returns
        -------
        :class:`compas.datastructures.Mesh`
            The collision geometry of the element.

        """
        points, faces = self.geometry.to_vertices_and_faces()
        faces = convex_hull(points)
        self._collision_mesh = Mesh.from_vertices_and_faces(points, faces)
        return Mesh.from_vertices_and_faces(points, faces)

    def transform(self, transformation):
        """Transforms all the attrbutes of the class.

        Parameters
        ----------
        transformation : :class:`compas.geometry.Transformation`
            The transformation to be applied to the Element's geometry and frames.

        Returns
        -------
        None

        """
        self.frame.transform(transformation)
        self.geometry_simplified.transform(transformation)
        self.geometry.transform(transformation)

        # I do not see the other way than to check the private property.
        # Otherwise it gets computed and transformed twice.
        # Also, we do not want to have these properties computed, unless needed.
        # It can be done above geometry transformations, but they will be computed.
        if self._aabb:
            self.compute_aabb()

        if self._obb:
            self.obb.transform(transformation)

        if self._collision_mesh:
            self.transform(transformation)

        if self._face_polygons:
            for polygon in self.face_polygons:
                polygon.transform(transformation)

    # ==========================================================================
    # Custom attributes and methods specific to this class.
    # ==========================================================================

    @property
    def face_polygons(self):
        if not self._face_polygons:
            self._face_polygons = self._compute_face_polygons()
        return self._face_polygons

    def _compute_face_polygons(self):
        """Computes the face polygons of the element.

        Returns
        -------
        list
            The face polygons of the element.

        """

        if hasattr(self, "_face_polygons"):
            return self._face_polygons

        # --------------------------------------------------------------------------
        # get polylines from the mesh faces
        # --------------------------------------------------------------------------
        self._face_polygons = []
        for g in self.geometry:
            if isinstance(g, Mesh):
                temp = self.geometry[0].to_polygons()
                self._face_polygons = []
                for point_list in temp:
                    self._face_polygons.append(Polygon(point_list))

        return self._face_polygons
