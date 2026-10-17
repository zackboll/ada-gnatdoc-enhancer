--  Fixed-length, value-semantic vector with a compile-time length.
--
--  Instantiating this package fixes the element type and the number of
--  components.
--
--  Vector is an ordinary Ada array and this generic does not introduce an
--  OpenCV native handle of its own. Array assignment follows Ada assignment
--  semantics for the actual element type. Element copying, adjustment,
--  finalization, and resource ownership depend on the type supplied when the
--  generic is instantiated.
--
--  Element_Type is the type of each element. Length is the number of
--  components and must be positive; component indices therefore range from
--  zero through Length - 1.
--  @formal Element_Type Type of each vector element.
--  @formal Length Number of components. Must be positive.

generic
   --  Type of each vector element.
   type Element_Type is private;
   --  Number of components. Must be positive.
   Length : Positive;
package OpenCV.Core.Vectors is

   --  Zero-based component index, from 0 through Length - 1.
   subtype Component_Index is Natural range 0 .. Length - 1;

   --  Vector of Length components, indexed from zero through Length - 1.
   type Vector is array (Component_Index) of Element_Type;

end OpenCV.Core.Vectors;
