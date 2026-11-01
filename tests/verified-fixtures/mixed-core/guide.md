# Verified calls

Authentic complete landing unit, followed by an original ownership-guide fragment.
The prose `Image.Clone` and `Create (2, 3, ...)` is not compiler evidence.

```ada
with OpenCV.Core;

procedure Example is
   use OpenCV.Core;
   Image : constant Mat := Create (2, 3, (Depth => UInt8, Channels => 1));
   Copy  : constant Mat := Image.Clone;
begin
   pragma Assert (Copy.Rows = 2 and then Copy.Columns = 3);
end Example;
```

## Incomplete and ambiguous

```ada
Image : Mat :=
  Create
    (Dimensions   => (Width => 640, Height => 480),
     Element_Type => (Depth => Float32, Channels => 1));

Dims : constant OpenCV.Size := Image.Dimensions;
```

```ada
Copy := Image.Clone;
```

```sh
echo "Image.Clone and Create (2, 3, ...)"
```

```text
Copy.Rows and Copy.Columns are ordinary text.
```
