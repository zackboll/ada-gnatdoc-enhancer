procedure Dispatch is
   package Types is
      type Root is tagged null record;
      function Value (Self : Root) return Integer is (1);
      type Child is new Root with null record;
      overriding function Value (Self : Child) return Integer is (2);
   end Types;
   use Types;
   procedure Invoke (Self : Root'Class) is
      Answer : Integer := Value (Self);
   begin
      pragma Assert (Answer in 1 .. 2);
   end Invoke;
   Object : Child;
begin
   Invoke (Object);
end Dispatch;