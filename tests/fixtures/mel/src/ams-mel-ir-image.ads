with AMS.MEL.IR;
package AMS.MEL.IR.Image is
   type Full_Frame is private;
   function Receive (Object : AMS.MEL.IR.Image_Stream; Timeout_Milliseconds : Natural := 0) return Full_Frame;
end AMS.MEL.IR.Image;
