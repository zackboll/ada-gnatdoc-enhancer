with OpenCV.Core.Int32_Vec2;

--  Zero-copy, callback-scoped access to the complete element buffer of a
--  continuous two-channel Int32 (CV_32SC2) Mat of any dimension count. The
--  view aliases native storage and is valid only during the callback. Every
--  operation validates the Mat's depth, channel count and continuity and
--  raises OpenCV_Error on any mismatch, before the callback is invoked.

package OpenCV.Core.Int32_Vec2_Buffer_Access is

   --  The flat element buffer of a Mat, one Int32_Vec2.Vector per Mat
   --  element, in OpenCV element order with the final dimension varying
   --  fastest. Each entry is one complete C2 element of a continuous Mat.
   --  For a nonempty Mat the callbacks pass arrays whose bounds are
   --  0 .. Natural (Image.Total) - 1.
   type Buffer_Array is array (Natural range <>) of Int32_Vec2.Vector;

   --  Invokes Process with a zero-copy view of a continuous two-channel
   --  Int32 Mat of any dimension count. Data aliases native storage for the
   --  entire logical buffer and is valid only during the callback. An empty
   --  Mat of the correct type is accepted and Process receives an empty Data.
   --  @param Image A continuous Int32 Mat with exactly two channels.
   --  @param Process Callback that receives the borrowed buffer. Data is
   --  valid only during the call and must not be retained.
   --  @exception OpenCV_Error Raised, before Process is invoked, when Image
   --  is not an Int32 two-channel Mat or is nonempty and not continuous,
   --  or has more elements than Natural'Last.
   procedure With_Read_Only_Buffer
     (Image   : Mat;
      Process : not null access procedure (Data : aliased Buffer_Array));

   --  As With_Read_Only_Buffer, except Process receives an in-out view.
   --  Writes through Data mutate the actual Mat storage immediately.
   --  @param Image A continuous Int32 Mat with exactly two channels.
   --  @param Process Callback that receives the borrowed buffer for reading
   --  and writing. Data is valid only during the call and must not be
   --  retained.
   --  @exception OpenCV_Error Raised, before Process is invoked, when Image
   --  is not an Int32 two-channel Mat or is nonempty and not continuous,
   --  or has more elements than Natural'Last.
   procedure With_Writable_Buffer
     (Image   : in out Mat;
      Process :
        not null access procedure (Data : aliased in out Buffer_Array));
end OpenCV.Core.Int32_Vec2_Buffer_Access;
