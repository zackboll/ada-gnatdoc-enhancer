with OpenCV.Core.Vectors;

--  One complete CV_8UC3 Mat element (3 bytes). Components 0 .. 2 are OpenCV
--  channel indices holding unsigned 0 .. 255 values; no semantic channel
--  meaning (such as blue-green-red order) is assigned. It corresponds to the
--  native Vec3b (uchar) alias.
package OpenCV.Core.UInt8_Vec3 is new
  OpenCV.Core.Vectors (Element_Type => UInt8_Value, Length => 3);
