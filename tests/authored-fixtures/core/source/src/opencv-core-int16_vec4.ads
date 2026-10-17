with OpenCV.Core.Vectors;

--  One complete CV_16SC4 Mat element (8 bytes). Components 0 .. 3 are OpenCV
--  channel indices holding signed -32768 .. 32767 values; no semantic
--  channel meaning is assigned. It corresponds to the native Vec4s (short)
--  alias.
package OpenCV.Core.Int16_Vec4 is new
  OpenCV.Core.Vectors (Element_Type => Int16_Value, Length => 4);
