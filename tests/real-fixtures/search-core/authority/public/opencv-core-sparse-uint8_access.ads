--  Typed access to the elements of a single-channel UInt8 (CV_8UC1)
--  Sparse_Mat. Each operation validates that the matrix is allocated and has
--  exactly this depth and channel count, then validates the coordinates, and
--  raises OpenCV_Error on any mismatch. Coordinates are zero-based, one per
--  dimension. Only stored nodes occupy memory: a missing coordinate reads as
--  zero but is not the same as a stored zero (see Contains and
--  Stored_Element_Count in the parent package). Writes go to the shared
--  nodes, so every shallow alias of the Sparse_Mat observes them.

package OpenCV.Core.Sparse.UInt8_Access is

   --  Reads the element at Indices. A missing node reads as zero and is not
   --  created.
   --  @param Image An allocated UInt8 Sparse_Mat with exactly one channel.
   --  @param Indices One zero-based index per dimension, each less than the
   --  matching extent.
   --  @return The stored value, or zero when no node is stored there.
   --  @exception OpenCV_Error Raised when Image is unallocated or has another
   --  depth or channel count, Indices does not have exactly Dimension_Count
   --  entries, or an index is out of bounds, or OpenCV reports a failure.
   function Get (Image : Sparse_Mat; Indices : Index_Array) return UInt8_Value;

   --  Stores Value at Indices, inserting the node if it is absent. A zero
   --  Value is still stored as an explicit node, which then counts in
   --  Stored_Element_Count and is visited by For_Each_Stored.
   --  @param Image An allocated UInt8 Sparse_Mat with exactly one channel.
   --  @param Indices One zero-based index per dimension, each less than the
   --  matching extent.
   --  @param Value The element value to store.
   --  @exception OpenCV_Error Raised when Image is unallocated or has another
   --  depth or channel count, Indices does not have exactly Dimension_Count
   --  entries, or an index is out of bounds, or OpenCV reports a failure.
   procedure Set
     (Image : in out Sparse_Mat; Indices : Index_Array; Value : UInt8_Value);

   --  Stored nodes only, in unspecified order. Indices are zero-based
   --  with bounds 1 .. Dimension_Count. Do not structurally mutate Image or a
   --  shallow alias during the callback. No native iterator escapes this call.
   --  The values passed to Process are copies.
   --  @param Image An allocated UInt8 Sparse_Mat with exactly one channel.
   --  @param Process Callback invoked once for each stored node, including
   --  explicitly stored zeros, with that node's coordinates and value.
   --  @exception OpenCV_Error Raised before any callback when Image is
   --  unallocated or has another depth or channel count, and also raised if
   --  the native iteration fails, which can happen after earlier callbacks
   --  have already run.
   procedure For_Each_Stored
     (Image   : Sparse_Mat;
      Process :
        not null access procedure
          (Indices : Index_Array; Value : UInt8_Value));
end OpenCV.Core.Sparse.UInt8_Access;
