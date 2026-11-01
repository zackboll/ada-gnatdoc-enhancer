with Overloads; use Overloads;
with Other; use Other;
procedure Valid is
   M : Mat;
   U : UMat;
   MC : Mat := M.Clone;
   UC : UMat := U.Clone;
   A : Integer := Pick (1);
   B : Integer := Pick ("two");
   C : Integer := Count (1);
   D : Integer := Count (1, 2);
   E : Integer := Named (Right => "x", Left => 1);
   F : Integer := Named (Right => 1, Left => "x");
   G : Integer := Defaulted (1);
   H : Integer := Result;
   S : String := Result;
   I : Integer := Overloads.Pick (3);
   J : Integer := Pick (True);



begin
   declare
      function Pick (Value : Integer) return Integer is (Value + 10);
      Shadowed : Integer := Pick (7);
   begin
      pragma Assert (Shadowed = 17);
   end;
   pragma Assert (A = 1 and B = 3 and C = 1 and D = 3 and E = 2 and F = 2);
   pragma Assert (G = 1 and H = 1 and S = "one" and I = 3 and J = 1);
   pragma Assert (MC in Mat and UC in UMat);
end Valid;
