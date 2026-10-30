with OpenCV.Core.Vectors;

--  One complete CV_16UC4 Mat element (8 bytes). Components 0 .. 3 are OpenCV
--  channel indices holding unsigned 0 .. 65535 values; no semantic channel
--  meaning is assigned. It corresponds to the native Vec4w (ushort) alias.
package OpenCV.Core.UInt16_Vec4 is new
  OpenCV.Core.Vectors (Element_Type => UInt16_Value, Length => 4);
