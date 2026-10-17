with OpenCV.Core.Vectors;

--  One complete CV_32SC4 Mat element (16 bytes). Components 0 .. 3 are
--  OpenCV channel indices holding signed 32-bit integers; no semantic
--  channel meaning is assigned. It corresponds to the native Vec4i (int)
--  alias.
package OpenCV.Core.Int32_Vec4 is new
  OpenCV.Core.Vectors (Element_Type => Int32_Value, Length => 4);
