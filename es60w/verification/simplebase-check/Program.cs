using System.Reflection;
using System.Runtime.Loader;
using System.Text;
using System.Text.Json;
// Compare actual old NuGet assembly API with the source-built replacement,
// then exercise RFC 4648 vectors and deterministic byte-array round trips.
var old = new AssemblyLoadContext("old", true).LoadFromAssemblyPath(Path.GetFullPath(args[0]));
var current = new AssemblyLoadContext("current", true).LoadFromAssemblyPath(Path.GetFullPath(args[1]));
HashSet<string> Api(Assembly a) => a.GetExportedTypes().SelectMany(t =>
    t.GetMembers(BindingFlags.Public | BindingFlags.Instance | BindingFlags.Static | BindingFlags.DeclaredOnly)
     .Select(m => t.FullName + ":" + m.MemberType + ":" + m.ToString())).ToHashSet();
var missing = Api(old).Except(Api(current)).ToArray();
if(missing.Length != 0) throw new Exception("Missing public API: " + string.Join("; ", missing));
if(old.GetName().Version != current.GetName().Version) throw new Exception("Assembly ABI version changed");
var type = current.GetType("SimpleBase.Base32", true)!;
var instance = type.GetField("Rfc4648")!.GetValue(null);
var encode = type.GetMethod("Encode")!; var decode = type.GetMethod("Decode")!;
string Encode(byte[] b) => (string)encode.Invoke(instance, new object[]{b, true})!;
byte[] Decode(string s) => (byte[])decode.Invoke(instance, new object[]{s})!;
var inputs = new[]{"", "f", "fo", "foo", "foob", "fooba", "foobar"};
var expected = new[]{"", "MY======", "MZXQ====", "MZXW6===", "MZXW6YQ=", "MZXW6YTB", "MZXW6YTBOI======"};
for(int i=0;i<inputs.Length;i++) if(Encode(Encoding.ASCII.GetBytes(inputs[i])) != expected[i]) throw new Exception("RFC vector " + i);
var random = new Random(60);for(int n=0;n<1025;n++){
 var b=new byte[n]; random.NextBytes(b);if(!Decode(Encode(b)).SequenceEqual(b)) throw new Exception("Round trip " + n);
}
Console.WriteLine(JsonSerializer.Serialize(new {public_api_compatible=true, assembly_version=current.GetName().Version!.ToString(), rfc4648_vectors=7, round_trips=1025, device_commands=0}));
