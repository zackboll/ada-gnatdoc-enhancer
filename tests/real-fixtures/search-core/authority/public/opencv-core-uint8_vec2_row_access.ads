with OpenCV.Core.UInt8_Vec2;

--  Whole-row access to two-channel UInt8 (CV_8UC2) two-dimensional Mats,
--  by copy (Read_Row, Write_Row) or by a zero-copy callback-scoped view
--  (With_Read_Only_Row, With_Writable_Row). Each row element is one complete
--  OpenCV.Core.UInt8_Vec2.Vector. Row and column indices are zero-based.
--  Every operation validates the Mat's depth, channel count, row index and
--  row length and raises OpenCV_Error on any mismatch.

package OpenCV.Core.UInt8_Vec2_Row_Access is

   --  The pixels of one Mat row, one UInt8_Vec2.Vector per column. Array
   --  bounds are the caller's choice: only the length matters, and the first
   --  array element always corresponds to column 0. The zero-copy callbacks
   --  pass arrays whose bounds are 0 .. Image.Columns - 1.
   type Row_Array is array (Natural range <>) of UInt8_Vec2.Vector;

   --  Copies one row of Image into Data. Data'Length must equal
   --  Image.Columns; Data (Data'First) receives column 0 and the array's
   --  index bounds are otherwise irrelevant. Image is unchanged and Data
   --  owns its values.
   --  @param Image A two-dimensional UInt8 Mat with exactly two channels.
   --  @param Row Zero-based row, in 0 .. Image.Rows - 1.
   --  @param Data Receives one two-channel pixel per column.
   --  @exception OpenCV_Error Raised when Image is not a UInt8 two-channel
   --  two-dimensional Mat, Row is outside the Mat, or Data'Length differs
   --  from Image.Columns.
   procedure Read_Row (Image : Mat; Row : Natural; Data : out Row_Array);

   --  Copies Data into one row of Image. Data'Length must equal
   --  Image.Columns; Data (Data'First) is stored in column 0. The values are
   --  written to the Mat's actual storage, so shallow aliases and the parent
   --  of a Region observe them.
   --  @param Image A two-dimensional UInt8 Mat with exactly two channels.
   --  @param Row Zero-based row, in 0 .. Image.Rows - 1.
   --  @param Data One two-channel pixel per column.
   --  @exception OpenCV_Error Raised when Image is not a UInt8 two-channel
   --  two-dimensional Mat, Row is outside the Mat, or Data'Length differs
   --  from Image.Columns.
   procedure Write_Row (Image : in out Mat; Row : Natural; Data : Row_Array);

   --  Callback-scoped zero-copy borrow of one UInt8 C2 Mat row; Data aliases
   --  native storage, each element is one complete C2 pixel, and Data is
   --  indexed 0 .. Image.Columns - 1. A shallow lease protects the storage
   --  until Process returns. Do not retain a reference or address of Data
   --  after Process returns.
   --  @param Image A two-dimensional UInt8 Mat with exactly two channels.
   --  @param Row Zero-based row, in 0 .. Image.Rows - 1.
   --  @param Process Callback that receives the borrowed row. Data is valid
   --  only during the call and must not be retained.
   --  @exception OpenCV_Error Raised, before Process is invoked, when Image
   --  is not a two-dimensional UInt8 two-channel Mat or Row is outside the
   --  Mat.
   procedure With_Read_Only_Row
     (Image   : Mat;
      Row     : Natural;
      Process : not null access procedure (Data : aliased Row_Array));

   --  As With_Read_Only_Row, except Process receives an in-out view. Writes
   --  through Data mutate the actual Mat storage immediately, with no
   --  write-back phase.
   --  @param Image A two-dimensional UInt8 Mat with exactly two channels.
   --  @param Row Zero-based row, in 0 .. Image.Rows - 1.
   --  @param Process Callback that receives the borrowed row for reading and
   --  writing. Data is valid only during the call and must not be retained.
   --  @exception OpenCV_Error Raised, before Process is invoked, when Image
   --  is not a two-dimensional UInt8 two-channel Mat or Row is outside the
   --  Mat.
   procedure With_Writable_Row
     (Image   : in out Mat;
      Row     : Natural;
      Process : not null access procedure (Data : aliased in out Row_Array));

end OpenCV.Core.UInt8_Vec2_Row_Access;
