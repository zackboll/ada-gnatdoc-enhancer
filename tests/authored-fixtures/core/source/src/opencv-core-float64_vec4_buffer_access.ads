with OpenCV.Core.Float64_Vec4;

--  Zero-copy, callback-scoped access to the complete element buffer of a
--  continuous four-channel Float64 (CV_64FC4) Mat of any dimension count.
--  The view aliases native storage and is valid only during the callback.
--  Every operation validates the Mat's depth, channel count and continuity
--  and raises OpenCV_Error on any mismatch, before the callback is invoked.

package OpenCV.Core.Float64_Vec4_Buffer_Access is

   --  The flat element buffer of a Mat: one four-channel vector per Mat
   --  element, in OpenCV element order with the final dimension varying
   --  fastest. The callbacks pass arrays whose bounds are
   --  0 .. Natural (Image.Total) - 1.
   type Buffer_Array is array (Natural range <>) of Float64_Vec4.Vector;

   --  Callback-scoped zero-copy borrow of a continuous Float64 C4 Mat of
   --  any dimension count; genuine N-D Mats are supported. Data is one
   --  flat zero-based array, Data'Length = Natural (Image.Total), in
   --  OpenCV element order with the final dimension varying fastest; for
   --  a 2-D Mat, Data (Row * Image.Columns + Column) is (Row, Column).
   --  One entry per complete C4 element; channels are never flattened.
   --  Non-continuous Mats (gapped Regions or Slices) raise OpenCV_Error
   --  before Process runs. A shallow Mat lease keeps the storage alive
   --  (memory lifetime, not synchronization); writes are immediately
   --  visible. Do not retain Data after the callback returns.
   --  @param Image A continuous Float64 Mat with exactly four channels.
   --  @param Process Callback that receives the borrowed buffer. Data is
   --  valid only during the call and must not be retained.
   --  @exception OpenCV_Error Raised, before Process is invoked, when Image
   --  is not a Float64 four-channel Mat or is nonempty and not continuous,
   --  or has more elements than Natural'Last.
   procedure With_Read_Only_Buffer
     (Image   : Mat;
      Process : not null access procedure (Data : aliased Buffer_Array));

   --  As With_Read_Only_Buffer, except Process receives an in-out view.
   --  Writes through Data mutate the actual Mat storage immediately.
   --  @param Image A continuous Float64 Mat with exactly four channels.
   --  @param Process Callback that receives the borrowed buffer for reading
   --  and writing. Data is valid only during the call and must not be
   --  retained.
   --  @exception OpenCV_Error Raised, before Process is invoked, when Image
   --  is not a Float64 four-channel Mat or is nonempty and not continuous,
   --  or has more elements than Natural'Last.
   procedure With_Writable_Buffer
     (Image   : in out Mat;
      Process :
        not null access procedure (Data : aliased in out Buffer_Array));
end OpenCV.Core.Float64_Vec4_Buffer_Access;
