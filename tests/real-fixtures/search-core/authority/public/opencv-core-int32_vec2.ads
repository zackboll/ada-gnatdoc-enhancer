with OpenCV.Core.Vectors;

--  One complete CV_32SC2 Mat element (8 bytes). Components 0 .. 1 are OpenCV
--  channel indices holding signed 32-bit integers; no semantic channel
--  meaning is assigned. It corresponds to the native Vec2i (int) alias.
package OpenCV.Core.Int32_Vec2 is new
  OpenCV.Core.Vectors (Element_Type => Int32_Value, Length => 2);
