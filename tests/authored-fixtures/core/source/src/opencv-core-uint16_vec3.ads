with OpenCV.Core.Vectors;

--  One complete CV_16UC3 Mat element (6 bytes). Components 0 .. 2 are OpenCV
--  channel indices holding unsigned 0 .. 65535 values; no semantic channel
--  meaning is assigned. It corresponds to the native Vec3w (ushort) alias.
package OpenCV.Core.UInt16_Vec3 is new
  OpenCV.Core.Vectors (Element_Type => UInt16_Value, Length => 3);
