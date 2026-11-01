with OpenCV.Core;

procedure Example is
   use OpenCV.Core;
   Image : constant Mat := Create (2, 3, (Depth => UInt8, Channels => 1));
   Copy  : constant Mat := Image.Clone;
begin
   pragma Assert (Copy.Rows = 2 and then Copy.Columns = 3);
end Example;
