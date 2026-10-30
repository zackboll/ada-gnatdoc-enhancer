with OpenCV.Core.Vectors;

--  One complete CV_16SC3 Mat element (6 bytes). Components 0 .. 2 are OpenCV
--  channel indices holding signed -32768 .. 32767 values; no semantic
--  channel meaning is assigned. It corresponds to the native Vec3s (short)
--  alias.
package OpenCV.Core.Int16_Vec3 is new
  OpenCV.Core.Vectors (Element_Type => Int16_Value, Length => 3);
