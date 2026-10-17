with OpenCV.Core.UInt16_Vec2;

--  Zero-copy, callback-scoped access to the complete element buffer of a
--  continuous two-channel UInt16 (CV_16UC2) Mat of any dimension count. Each
--  buffer entry is one complete two-channel pixel. The view aliases native
--  storage and is valid only during the callback. Every operation validates
--  the Mat's depth, channel count and continuity and raises OpenCV_Error on
--  any mismatch, before the callback is invoked.

package OpenCV.Core.UInt16_Vec2_Buffer_Access is

   --  The flat element buffer of a Mat: one UInt16_Vec2.Vector per Mat
   --  element, in OpenCV element order with the final dimension varying
   --  fastest.
   type Buffer_Array is array (Natural range <>) of UInt16_Vec2.Vector;

   --  Each entry is one complete C2 element; borrow is callback-scoped.
   --  Data is a flat array of all Mat elements, in OpenCV element order with
   --  the final dimension varying fastest. A shallow lease retains storage
   --  until Process returns. An empty Mat of the right type is accepted.
   --  @param Image A continuous UInt16 Mat with exactly two channels.
   --  @param Process Callback that receives the borrowed buffer. Data is
   --  valid only during the call and must not be retained.
   --  @exception OpenCV_Error Raised, before Process is invoked, when Image
   --  is not a UInt16 two-channel Mat or is nonempty and not continuous,
   --  or has more elements than Natural'Last.
   procedure With_Read_Only_Buffer
     (Image   : Mat;
      Process : not null access procedure (Data : aliased Buffer_Array));

   --  As With_Read_Only_Buffer, except Process receives an in-out view whose
   --  writes mutate the actual Mat storage immediately.
   --  @param Image A continuous UInt16 Mat with exactly two channels.
   --  @param Process Callback that receives the borrowed buffer for reading
   --  and writing. Data is valid only during the call and must not be
   --  retained.
   --  @exception OpenCV_Error Raised, before Process is invoked, when Image
   --  is not a UInt16 two-channel Mat or is nonempty and not continuous,
   --  or has more elements than Natural'Last.
   procedure With_Writable_Buffer
     (Image   : in out Mat;
      Process :
        not null access procedure (Data : aliased in out Buffer_Array));
end OpenCV.Core.UInt16_Vec2_Buffer_Access;
