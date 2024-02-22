import compas

if not compas.IPY:
    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from compas_model.model import ElementNode  # noqa: F401

import compas.geometry
import compas.datastructures  # noqa: F401

from compas.data import Data


class Feature(Data):
    """Base class for all element features.

    Parameters
    ----------
    name : str, optional
        The name of the feature.

    """

    @property
    def __data__(self):
        # type: () -> dict
        return {}

    def __init__(self, name=None):
        # type: (str | None) -> None
        super(Feature, self).__init__(name=name)

    def apply(self, shape):
        # type: (compas.datastructures.Mesh | compas.geometry.Brep) -> compas.datastructures.Mesh | compas.geometry.Brep
        raise NotImplementedError


class Element(Data):
    """Base class for all elements in the model.

    Parameters
    ----------
    geometry : :class:`compas.geometry.Shape` | :class:`compas.geometry.Brep` | :class:`compas.datastructures.Mesh`, optional
        The complete geometry of the element.
    frame : None, default WorldXY
        The frame of the element.
    name : None
        The name of the element.

    Attributes
    ----------
    graph_node : int
        The identifier of the corresponding node in the interaction graph of the parent model.
    tree_node : :class:`compas.datastructures.TreeNode`
        The node in the hierarchical element tree of the parent model.
    frame : :class:`compas.geometry.Frame`
        The local coordinate frame of the element.
    geometry : :class:`compas.datastructures.Mesh` | :class:`compas.geometry.Brep`, readonly
        The geometry of the element, computed from the base shape and its features.
    aabb : :class:`compas.geometry.Box`, readonly
        The Axis Aligned Bounding Box (AABB) of the element.
    obb : :class:`compas.geometry.Box`, readonly
        The Oriented Bounding Box (OBB) of the element.
    collision_mesh : :class:`compas.datastructures.Mesh`, readonly
        The collision geometry of the element.

    """

    @property
    def __data__(self):
        # type: () -> dict
        return {"frame": self.frame, "name": self.name}

    def __init__(self, geometry=None, frame=None, name=None):
        # type: (compas.geometry.Shape | compas.geometry.Brep | compas.datastructures.Mesh | None, compas.geometry.Frame | None, str | None) -> None

        super(Element, self).__init__(name=name)
        self.graph_node = None  # type: int | None
        self.tree_node = None  # type: ElementNode | None
        self._aabb = None
        self._obb = None
        self._collision_mesh = None
        self._geometry = geometry
        self._frame = frame

    def __repr__(self):
        # type: () -> str
        return "Element(frame={!r}, name={})".format(self.frame, self.name)

    def __str__(self):
        # type: () -> str
        return "<Element {}>".format(self.name)

    @property
    def frame(self):
        # type: () -> compas.geometry.Frame | None
        return self._frame

    @frame.setter
    def frame(self, frame):
        self._frame = frame

    # ==========================================================================
    # Computed attributes
    # ==========================================================================

    @property
    def geometry(self):
        if self._geometry is None:
            self._geometry = self.compute_geometry()
        return self._geometry

    @property
    def aabb(self):
        # type: () -> compas.geometry.Box
        if not self._aabb:
            self._aabb = self.compute_aabb()
        return self._aabb

    @property
    def obb(self):
        # type: () -> compas.geometry.Box
        if not self._obb:
            self._obb = self.compute_obb()
        return self._obb

    @property
    def dimensions(self):
        # type: () -> tuple[float, float, float]
        return self.obb.width, self.obb.height, self.obb.depth

    @property
    def collision_mesh(self):
        # type: () -> compas.datastructures.Mesh
        if not self._collision_mesh:
            self._collision_mesh = self.compute_collision_mesh()
        return self._collision_mesh

    # ==========================================================================
    # Abstract methods
    # ==========================================================================

    def compute_geometry(self, include_features=False):
        # type: (bool) -> compas.datastructures.Mesh | compas.geometry.Brep
        """Compute the geometry of the element.

        Parameters
        ----------
        include_features : bool, optional
            If ``True``, include the features in the computed geometry.
            If ``False``, return only the base geometry.

        Returns
        -------
        :class:`compas.datastructures.Mesh` | :class:`compas.geometry.Brep`

        """
        raise NotImplementedError

    def compute_aabb(self, inflate=0.0):
        # type: (float | None) -> compas.geometry.Box
        """Computes the Axis Aligned Bounding Box (AABB) of the element.

        Parameters
        ----------
        inflate : float, optional
            Offset of box to avoid floating point errors.

        Returns
        -------
        :class:`compas.geometry.Box`
            The AABB of the element.

        """
        raise NotImplementedError

    def compute_obb(self, inflate=0.0):
        # type: (float | None) -> compas.geometry.Box
        """Computes the Oriented Bounding Box (OBB) of the element.

        Parameters
        ----------
        inflate : float
            Offset of box to avoid floating point errors.

        Returns
        -------
        :class:`compas.geometry.Box`
            The OBB of the element.

        """
        raise NotImplementedError

    def compute_collision_mesh(self):
        # type: () -> compas.datastructures.Mesh
        """Computes the collision geometry of the element.

        Returns
        -------
        :class:`compas.datastructures.Mesh`
            The collision geometry of the element.

        """
        raise NotImplementedError

    def transform(self, transformation):
        # type: (compas.geometry.Transformation) -> None
        """Transforms all the attrbutes of the class.

        Parameters
        ----------
        transformation : :class:`compas.geometry.Transformation`
            The transformation to be applied to the Element's geometry and frames.

        Returns
        -------
        None

        """
        raise NotImplementedError

    # ==========================================================================
    # Methods
    # ==========================================================================

    def transformed(self, transformation):
        # type: (compas.geometry.Transformation) -> Element
        """Creates a transformed copy of the class.

        Parameters
        ----------
        transformation : :class:`compas.geometry.Transformation`:
            The transformation to be applied to the copy of an element.

        Returns
        -------
        :class:`compas_model.elements.Element`
            A new instance of the Element with the specified transformation applied.

        """
        element = self.copy()
        element.transform(transformation)
        return element
