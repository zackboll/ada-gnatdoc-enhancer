with OpenCV.Core.Float16_Vec4;

--  Zero-copy, callback-scoped access to the complete element buffer of a
--  continuous four-channel Float16 (CV_16FC4) Mat of any dimension count.
--  Each element is one complete four-channel pixel whose components are the
--  exact stored IEEE-754 binary16 encodings. The view aliases native storage
--  and is valid only during the callback. Every operation validates the
--  Mat's depth, channel count and continuity and raises OpenCV_Error on any
--  mismatch, before the callback is invoked.

package OpenCV.Core.Float16_Vec4_Buffer_Access is

   --  The flat pixel buffer of a Mat: one Vector (four interleaved channel
   --  values) per Mat element, in OpenCV element order with the final
   --  dimension varying fastest. The callbacks pass arrays whose bounds are
   --  0 .. Natural (Image.Total) - 1.
   type Buffer_Array is array (Natural range <>) of Float16_Vec4.Vector;

   --  Invokes Process with a zero-copy view of a continuous Float16 C4 Mat
   --  of any dimension count; genuine N-D Mats are supported. Data directly
   --  aliases native CV_16FC4 storage. Each Data element is one complete
   --  8-byte C4 element: Data (Index) (0 .. 3) are channels 0 .. 3; channels
   --  are never flattened into Data indexing. Each component is the exact
   --  stored IEEE-754 binary16 encoding; signed zeros, subnormals,
   --  infinities, and NaN payloads are not converted or canonicalized.
   --  Data'First = 0 and Data'Length = Natural (Image.Total), in OpenCV
   --  element order with the final dimension varying fastest. Image must be
   --  continuous; a nonempty non-continuous Mat (gapped Region or Slice)
   --  raises OpenCV_Error before Process is invoked. A shallow Mat lease
   --  keeps storage alive for the callback (memory management, not thread
   --  synchronization). Do not retain a reference or address of Data after
   --  Process returns.
   --  @param Image A continuous Float16 Mat with exactly four channels.
   --  @param Process Callback that receives the borrowed buffer. Data is
   --  valid only during the call and must not be retained.
   --  @exception OpenCV_Error Raised, before Process is invoked, when Image
   --  is not a Float16 four-channel Mat or is nonempty and not continuous,
   --  or has more elements than Natural'Last.
   procedure With_Read_Only_Buffer
     (Image   : Mat;
      Process : not null access procedure (Data : aliased Buffer_Array));

   --  As With_Read_Only_Buffer, except writes through Data mutate the Mat
   --  storage immediately. Exceptions raised by Process propagate unchanged;
   --  completed writes remain visible.
   --  @param Image A continuous Float16 Mat with exactly four channels.
   --  @param Process Callback that receives the borrowed buffer for reading
   --  and writing. Data is valid only during the call and must not be
   --  retained.
   --  @exception OpenCV_Error Raised, before Process is invoked, when Image
   --  is not a Float16 four-channel Mat or is nonempty and not continuous,
   --  or has more elements than Natural'Last.
   procedure With_Writable_Buffer
     (Image   : in out Mat;
      Process :
        not null access procedure (Data : aliased in out Buffer_Array));

end OpenCV.Core.Float16_Vec4_Buffer_Access;
