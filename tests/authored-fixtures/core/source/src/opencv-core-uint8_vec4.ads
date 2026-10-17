with OpenCV.Core.Vectors;

--  One complete CV_8UC4 Mat element (4 bytes). Components 0 .. 3 are OpenCV
--  channel indices holding unsigned 0 .. 255 values; no semantic channel
--  meaning is assigned. It corresponds to the native Vec4b (uchar) alias.
package OpenCV.Core.UInt8_Vec4 is new
  OpenCV.Core.Vectors (Element_Type => UInt8_Value, Length => 4);
