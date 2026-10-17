with OpenCV.Core.Vectors;

--  One complete CV_16SC2 Mat element (4 bytes). Components 0 .. 1 are OpenCV
--  channel indices holding signed -32768 .. 32767 values; no semantic
--  channel meaning is assigned. It corresponds to the native Vec2s (short)
--  alias.
package OpenCV.Core.Int16_Vec2 is new
  OpenCV.Core.Vectors (Element_Type => Int16_Value, Length => 2);
