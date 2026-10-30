with OpenCV.Core.Vectors;

--  One complete CV_16UC2 Mat element (4 bytes). Components 0 .. 1 are OpenCV
--  channel indices holding unsigned 0 .. 65535 values; no semantic channel
--  meaning is assigned. It corresponds to the native Vec2w (ushort) alias.
package OpenCV.Core.UInt16_Vec2 is new
  OpenCV.Core.Vectors (Element_Type => UInt16_Value, Length => 2);
