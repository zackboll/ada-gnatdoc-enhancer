with OpenCV.Core.Int8_Vec3;

--  Zero-copy, callback-scoped access to the complete element buffer of a
--  continuous three-channel Int8 (CV_8SC3) Mat of any dimension count. The
--  view aliases native storage and is valid only during the callback. Every
--  operation validates the Mat's depth, channel count and continuity and
--  raises OpenCV_Error on any mismatch, before the callback is invoked.

package OpenCV.Core.Int8_Vec3_Buffer_Access is

   --  The flat element buffer of a Mat: one complete three-channel vector
   --  per Mat element, in OpenCV element order with the final dimension
   --  varying fastest.
   type Buffer_Array is array (Natural range <>) of Int8_Vec3.Vector;

   --  Invokes Process with a zero-copy view of a continuous Int8 C3 Mat of
   --  any dimension count; genuine N-D Mats are supported. Data directly
   --  aliases native CV_8SC3 storage. Each Data element is one complete
   --  3-byte C3 element: Data (Index) (0 .. 2) are channels 0 .. 2 holding
   --  signed -128 .. 127 values; channels are never flattened into Data
   --  indexing. Data'First = 0 and Data'Length = Natural (Image.Total), in
   --  OpenCV element order with the final dimension varying fastest. Image
   --  must be continuous; a nonempty non-continuous Mat (gapped Region or
   --  Slice) raises OpenCV_Error before Process is invoked. A shallow Mat
   --  lease keeps storage alive for the callback (memory management, not
   --  thread synchronization). Do not retain a reference or address of Data
   --  after Process returns.
   --  @param Image A continuous Int8 Mat with exactly three channels.
   --  @param Process Callback that receives the borrowed buffer. Data is
   --  valid only during the call and must not be retained.
   --  @exception OpenCV_Error Raised, before Process is invoked, when Image
   --  is not an Int8 three-channel Mat or is nonempty and not continuous,
   --  or has more elements than Natural'Last.
   procedure With_Read_Only_Buffer
     (Image   : Mat;
      Process : not null access procedure (Data : aliased Buffer_Array));

   --  As With_Read_Only_Buffer, except writes through Data mutate the Mat
   --  storage immediately. Exceptions raised by Process propagate unchanged;
   --  completed writes remain visible.
   --  @param Image A continuous Int8 Mat with exactly three channels.
   --  @param Process Callback that receives the borrowed buffer for reading
   --  and writing. Data is valid only during the call and must not be
   --  retained.
   --  @exception OpenCV_Error Raised, before Process is invoked, when Image
   --  is not an Int8 three-channel Mat or is nonempty and not continuous,
   --  or has more elements than Natural'Last.
   procedure With_Writable_Buffer
     (Image   : in out Mat;
      Process :
        not null access procedure (Data : aliased in out Buffer_Array));

end OpenCV.Core.Int8_Vec3_Buffer_Access;
