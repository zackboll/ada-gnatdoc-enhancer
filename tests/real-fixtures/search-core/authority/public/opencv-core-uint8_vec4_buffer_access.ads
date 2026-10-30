with OpenCV.Core.UInt8_Vec4;

--  Zero-copy, callback-scoped access to the complete element buffer of a
--  continuous four-channel UInt8 (CV_8UC4) Mat of any dimension count. Each
--  buffer entry is one complete OpenCV.Core.UInt8_Vec4.Vector. The view
--  aliases native storage and is valid only during the callback. Every
--  operation validates the Mat's depth, channel count and continuity and
--  raises OpenCV_Error on any mismatch, before the callback is invoked.

package OpenCV.Core.UInt8_Vec4_Buffer_Access is

   --  The flat element buffer of a Mat: one UInt8_Vec4.Vector per Mat
   --  element, in OpenCV element order with the final dimension varying
   --  fastest. The callbacks pass arrays whose bounds are
   --  0 .. Natural (Image.Total) - 1.
   type Buffer_Array is array (Natural range <>) of UInt8_Vec4.Vector;

   --  Callback-scoped zero-copy view of a continuous UInt8 C4 Mat of any
   --  dimension count. Each entry is one complete C4 element; Data aliases
   --  native storage and is indexed 0 .. Natural (Image.Total) - 1. A
   --  shallow lease retains storage until Process returns. A nonempty
   --  non-continuous Mat is rejected; an empty Mat is accepted and Process
   --  then receives an empty Data. Do not retain a reference or address of
   --  Data after Process returns.
   --  @param Image A continuous UInt8 Mat with exactly four channels.
   --  @param Process Callback that receives the borrowed buffer. Data is
   --  valid only during the call and must not be retained.
   --  @exception OpenCV_Error Raised, before Process is invoked, when Image
   --  is not a UInt8 four-channel Mat or is nonempty and not continuous,
   --  or has more elements than Natural'Last.
   procedure With_Read_Only_Buffer
     (Image   : Mat;
      Process : not null access procedure (Data : aliased Buffer_Array));

   --  As With_Read_Only_Buffer, except Process receives an in-out view.
   --  Writes through Data mutate the actual Mat storage immediately, with no
   --  write-back phase.
   --  @param Image A continuous UInt8 Mat with exactly four channels.
   --  @param Process Callback that receives the borrowed buffer for reading
   --  and writing. Data is valid only during the call and must not be
   --  retained.
   --  @exception OpenCV_Error Raised, before Process is invoked, when Image
   --  is not a UInt8 four-channel Mat or is nonempty and not continuous,
   --  or has more elements than Natural'Last.
   procedure With_Writable_Buffer
     (Image   : in out Mat;
      Process :
        not null access procedure (Data : aliased in out Buffer_Array));

end OpenCV.Core.UInt8_Vec4_Buffer_Access;
