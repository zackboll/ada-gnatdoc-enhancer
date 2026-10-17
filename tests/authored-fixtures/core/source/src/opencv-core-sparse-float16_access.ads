--  Typed access to the elements of a single-channel Float16 (CV_16FC1)
--  Sparse_Mat. Each element is one Float16_Value, the exact binary16 bit
--  pattern, which is stored and loaded without numeric conversion. Each
--  operation validates that the matrix is allocated and has exactly this
--  depth and channel count, then validates the coordinates, and raises
--  OpenCV_Error on any mismatch. Coordinates are zero-based, one per
--  dimension. Only stored nodes occupy memory: a missing coordinate reads as
--  zero but is not the same as a stored zero (see Contains and
--  Stored_Element_Count in the parent package). Writes go to the shared
--  nodes, so every shallow alias of the Sparse_Mat observes them.

package OpenCV.Core.Sparse.Float16_Access is

   --  Reads the element at Indices. A missing node reads as zero and is not
   --  created.
   --  @param Image An allocated Float16 Sparse_Mat with exactly one channel.
   --  @param Indices One zero-based index per dimension, each less than the
   --  matching extent.
   --  @return The stored value with its exact bits, or zero when no node is
   --  stored there.
   --  @exception OpenCV_Error Raised when Image is unallocated or has another
   --  depth or channel count, Indices does not have exactly Dimension_Count
   --  entries, or an index is out of bounds, or OpenCV reports a failure.
   function Get
     (Image : Sparse_Mat; Indices : Index_Array) return Float16_Value;

   --  Stores Value at Indices, inserting the node if it is absent. The exact
   --  bit pattern of Value is stored. A zero Value is still stored as an
   --  explicit node, which then counts in Stored_Element_Count and is
   --  visited by For_Each_Stored.
   --  @param Image An allocated Float16 Sparse_Mat with exactly one channel.
   --  @param Indices One zero-based index per dimension, each less than the
   --  matching extent.
   --  @param Value The element value to store; its bits are kept exactly.
   --  @exception OpenCV_Error Raised when Image is unallocated or has another
   --  depth or channel count, Indices does not have exactly Dimension_Count
   --  entries, or an index is out of bounds, or OpenCV reports a failure.
   procedure Set
     (Image : in out Sparse_Mat; Indices : Index_Array; Value : Float16_Value);

   --  Stored nodes only; unspecified order; exact binary16 bits.
   --  Do not structurally mutate Image or aliases during callbacks. Indices
   --  are zero-based with bounds 1 .. Dimension_Count. The values passed to
   --  Process are copies.
   --  @param Image An allocated Float16 Sparse_Mat with exactly one channel.
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
          (Indices : Index_Array; Value : Float16_Value));
end OpenCV.Core.Sparse.Float16_Access;
