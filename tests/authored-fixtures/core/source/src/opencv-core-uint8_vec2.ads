with OpenCV.Core.Vectors;

--  One complete CV_8UC2 Mat element (2 bytes). Components 0 .. 1 are OpenCV
--  channel indices holding unsigned 0 .. 255 values; no semantic channel
--  meaning is assigned. It corresponds to the native Vec2b (uchar) alias.
package OpenCV.Core.UInt8_Vec2 is new
  OpenCV.Core.Vectors (Element_Type => UInt8_Value, Length => 2);
