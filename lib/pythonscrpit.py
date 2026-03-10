import re
import sys

def format_number(n_str):
    """Clean up float numbers - remove unnecessary trailing zeros."""
    try:
        val = float(n_str)
        # If it's a whole number, return as int
        if val == int(val):
            return str(int(val)) + ".0"
        return str(val)
    except ValueError:
        return n_str

def format_cubicTo_args(args):
    """Format cubicTo with 6 args into multi-line style if needed."""
    if len(args) != 6:
        return None
    # Use multi-line format
    lines = ["      cubicTo("]
    for i, a in enumerate(args):
        comma = "," if i < len(args) - 1 else ""
        lines.append(f"        {format_number(a)}{comma}")
    lines.append("      )")
    return "\n".join(lines)

def extract_paths(dart_code):
    """Extract path variable names and their operations from raw Flutter paint code."""
    # Find all path variable names (e.g., path_18, path_118)
    path_names = list(dict.fromkeys(re.findall(r'\b(path_\d+)\b', dart_code)))
    
    results = []
    
    for path_name in path_names:
        # Extract the path number
        path_num = path_name.split('_')[1]
        
        # Find all operations for this path
        # Match: path_X.method(args);
        pattern = rf'{re.escape(path_name)}\.(\w+)\(([^;]*)\);'
        ops = re.findall(pattern, dart_code, re.DOTALL)
        
        if not ops:
            continue
        
        lines = []
        lines.append(f"    // Path {path_num}")
        lines.append(f"    Path {path_name} = Path();")
        
        for method, args_str in ops:
            # Clean up args - remove whitespace and newlines
            args_str = re.sub(r'\s+', '', args_str)
            args = [a.strip() for a in args_str.split(',') if a.strip()]
            
            if method == 'moveTo':
                x, y = [format_number(a) for a in args[:2]]
                lines.append(f"    {path_name}.moveTo({x}, {y});")
            
            elif method == 'lineTo':
                x, y = [format_number(a) for a in args[:2]]
                lines.append(f"    {path_name}.lineTo({x}, {y});")
            
            elif method == 'cubicTo':
                formatted_args = [format_number(a) for a in args[:6]]
                # Check if any arg is long (has many decimal places)
                long_args = any(len(a) > 6 for a in formatted_args)
                if long_args:
                    lines.append(f"    {path_name}.cubicTo(")
                    for i, a in enumerate(formatted_args):
                        comma = "," if i < 5 else ""
                        lines.append(f"      {a}{comma}")
                    lines.append(f"    );")
                else:
                    lines.append(f"    {path_name}.cubicTo({', '.join(formatted_args)});")
            
            elif method == 'quadraticBezierTo':
                formatted_args = [format_number(a) for a in args[:4]]
                lines.append(f"    {path_name}.quadraticBezierTo({', '.join(formatted_args)});")
            
            elif method == 'arcToPoint':
                # Keep as-is but clean whitespace
                lines.append(f"    {path_name}.arcToPoint({args_str});")
            
            elif method == 'close':
                lines.append(f"    {path_name}.close();")
            
            else:
                # Generic fallback
                lines.append(f"    {path_name}.{method}({', '.join(args)});")
        
        lines.append(f"    output.add({path_name});")
        results.append('\n'.join(lines))
    
    return results

def convert_file(input_text):
    """Main conversion: strip paint code, keep only path definitions."""
    # Remove Paint, canvas.draw, and other non-path lines
    # Keep only lines that are path operations or blank
    path_blocks = extract_paths(input_text)
    
    if not path_blocks:
        return "// No paths found in input."
    
    return '\n\n'.join(path_blocks)

def main():
    if len(sys.argv) < 2:
        print("Usage: python convert_paths.py <input_file> [output_file]")
        print("\nExample: python convert_paths.py raw_paths.dart cleaned_paths.dart")
        print("\nAlternatively, pipe input: cat raw_paths.dart | python convert_paths.py -")
        sys.exit(1)
    
    input_path = sys.argv[1]
    
    if input_path == '-':
        input_text = sys.stdin.read()
    else:
        with open(input_path, 'r') as f:
            input_text = f.read()
    
    result = convert_file(input_text)
    
    if len(sys.argv) >= 3:
        output_path = sys.argv[2]
        with open(output_path, 'w') as f:
            f.write(result)
        print(f"✅ Written to {output_path}")
    else:
        print(result)

# ── Quick self-test ──────────────────────────────────────────────────────────
TEST_INPUT = """
    path_18.moveTo(74.5, 173.0);
    path_18.cubicTo(74.99,174.09,75.38,173.68,75.72,173.25000000000003);
    path_18.cubicTo(76.2,174.25000000000003,77.55,177.25000000000003,78.21,181.24000000000004);
    path_18.cubicTo(78.91,185.41000000000003,78.61,189.65000000000003,77.44,193.68000000000004);
    path_18.close();
Paint paint_18_stroke = Paint()..style=PaintingStyle.stroke..strokeWidth=2;
paint_18_stroke.color=Color(0xff000000).withOpacity(1.0);
paint_18_stroke.strokeCap = StrokeCap.round;
paint_18_stroke.strokeJoin = StrokeJoin.round;
canvas.drawPath(path_18,paint_18_stroke);

    path_19.moveTo(100.0, 200.0);
    path_19.lineTo(150.5, 250.5);
    path_19.cubicTo(160.0,260.0,170.12345678,270.0,180.0,280.0);
    path_19.close();
Paint paint_19_fill = Paint()..style=PaintingStyle.fill;
paint_19_fill.color=Color(0xffff0000).withOpacity(1.0);
canvas.drawPath(path_19,paint_19_fill);
"""

if __name__ == '__main__':
    if len(sys.argv) == 1:
        # Run self-test
        print("Running self-test...\n")
        print(convert_file(TEST_INPUT))
    else:
        main()