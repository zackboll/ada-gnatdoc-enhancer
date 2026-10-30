with OpenCV.Core.UInt16_Vec2;

--  Whole-row access to two-channel UInt16 (CV_16UC2) two-dimensional Mats,
--  by copy (Read_Row, Write_Row) or by a zero-copy callback-scoped view
--  (With_Read_Only_Row, With_Writable_Row). Each array element is one
--  complete two-channel pixel. Row and column indices are zero-based. Every
--  operation validates the Mat's depth, channel count, row index and row
--  length and raises OpenCV_Error on any mismatch.

package OpenCV.Core.UInt16_Vec2_Row_Access is

   --  The values of one Mat row, one UInt16_Vec2.Vector per column. Only the
   --  length matters: the first array element corresponds to column 0.
   type Row_Array is array (Natural range <>) of UInt16_Vec2.Vector;

   --  Copies one row of Image into Data. Data'Length must equal
   --  Image.Columns; Data (Data'First) receives column 0. Image is unchanged
   --  and Data owns its values.
   --  @param Image A two-dimensional UInt16 Mat with exactly two channels.
   --  @param Row Zero-based row, in 0 .. Image.Rows - 1.
   --  @param Data Receives one two-channel pixel per column.
   --  @exception OpenCV_Error Raised when Image is not a UInt16 two-channel
   --  Mat, Row is outside the Mat, or Data'Length differs from
   --  Image.Columns.
   procedure Read_Row (Image : Mat; Row : Natural; Data : out Row_Array);

   --  Copies Data into one row of Image. Data'Length must equal
   --  Image.Columns; Data (Data'First) is stored in column 0. The values are
   --  written to the Mat's actual storage, so shallow aliases and the parent
   --  of a Region observe them.
   --  @param Image A two-dimensional UInt16 Mat with exactly two channels.
   --  @param Row Zero-based row, in 0 .. Image.Rows - 1.
   --  @param Data One two-channel pixel per column.
   --  @exception OpenCV_Error Raised when Image is not a UInt16 two-channel
   --  Mat, Row is outside the Mat, or Data'Length differs from
   --  Image.Columns.
   procedure Write_Row (Image : in out Mat; Row : Natural; Data : Row_Array);

   --  Callback-scoped, zero-copy access to one row. Data aliases the native
   --  storage of that row (one complete two-channel pixel per element) and is
   --  valid only during Process; a shallow Mat lease keeps the storage alive
   --  for the callback.
   --  @param Image A two-dimensional UInt16 Mat with exactly two channels.
   --  @param Row Zero-based row, in 0 .. Image.Rows - 1.
   --  @param Process Callback that receives the borrowed row. Data is valid
   --  only during the call and must not be retained.
   --  @exception OpenCV_Error Raised, before Process is invoked, when Image
   --  is not a two-dimensional UInt16 two-channel Mat or Row is outside the
   --  Mat.
   procedure With_Read_Only_Row
     (Image   : Mat;
      Row     : Natural;
      Process : not null access procedure (Data : aliased Row_Array));

   --  As With_Read_Only_Row, except Process receives an in-out view whose
   --  writes mutate the actual Mat storage immediately.
   --  @param Image A two-dimensional UInt16 Mat with exactly two channels.
   --  @param Row Zero-based row, in 0 .. Image.Rows - 1.
   --  @param Process Callback that receives the borrowed row for reading and
   --  writing. Data is valid only during the call and must not be retained.
   --  @exception OpenCV_Error Raised, before Process is invoked, when Image
   --  is not a two-dimensional UInt16 two-channel Mat or Row is outside the
   --  Mat.
   procedure With_Writable_Row
     (Image   : in out Mat;
      Row     : Natural;
      Process : not null access procedure (Data : aliased in out Row_Array));
end OpenCV.Core.UInt16_Vec2_Row_Access;
