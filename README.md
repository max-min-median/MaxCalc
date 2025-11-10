# __MaxCalc__
This calculator started as an idea for a project for [REDACTED: name of a particular online course] which I felt would be difficult enough to test my own limits as well as be an actual functional tool that I would use for my day job (math tutor).
- Intended to perform quick algebraic calculations.
- Main feature: Flexible and 'loose' parsing of algebraic expressions, much like how one would write them out.

## Installation
1. Clone the repository.
2. Install windows dependancies
   ```
   pip install -r requirements.txt
   ```
3. Run `calculator.py`
   ```
   python calculator.py
   ```
-----------

## Commands

| Command | Description |
| ------- | ----------- |
| `help`  | shows this page |
| `vars`  | displays user-defined variables |
| `del [v1] [v2] ...` | deletes one or more user-defined variables |
| `prec N` | set working precision to `10^(-N)`, i.e. `N` decimal places |
| `disp N` | set final display precision to `N` decimal places |
| `frac N` | set length limit for fractions to be displayed |
| `keyboard \| kb [on/off]` | enables / disables keyboard module for detection of `Ctrl` / `Shift` |
| `debug [on/off]` | debug mode shows calculation steps |
| `sto[re] \| = \| -> <varName>` | store previous calculation into 'varName' |

## Editing

Common text-editor functionality is available, i.e.
- Holding `Ctrl` enables word-jump,
- Holding `Shift` enables selection.
- Backtick \` switches the active window. While the display window is active, use `up` and `down` to select, then `Enter` to paste into the input window.

| Hotkeys | Description |
| ------- | ----------- |
| `Shift + <Arrow>` | Text selection |
| `Ctrl + <Arrow>` | Jumps forward/backward by one word |
| `Ctrl + X / C / V` | Cut / Copy / Paste |
| `Ctrl + A` | Select all |
| `Ctrl + Bkspc` | Delete word at cursor |

-----------
## Things to try
| Input | Notes |
| ---------- | ----- |
| `2{3-4[5+65(3!` | Multiple bracket types are supported, and brackets are auto-closed |
| `x = 2; 2x + 1/x` | Semicolons separate expressions and evaluate to the rightmost expression |

- Whitespace has an effect on precedence. Some examples:

| Input | Notes |
| ---------- | ----- |
| `a = 2/3x; b = 2/3 x` | `a` evaluates as `2/(3x)`, `b` evaluates as `(2x)/3` |
| `a = sin pi/2; b = sinpi/2` | `a` evaluates as `sin (pi/2)`, `b` evaluates as `(sin pi)/2` |
| `4x^3/5` | evaluates as `(4x^3)/5` |
| `a = 1/2/3/4; b = 1/2 / 3/4; c = 1 / 2/3 / 4` | Give these a try! |

- The previous calculation is automatically stored as `ans`:

| Input | Notes |
| ---------- | ----- |
| `ans` | shows previous calculation |
| `2ans` (repeatedly) | number keeps doubling |
| `ans % 2 && 3ans + 1 \|\| ans / 2` (repeatedly) | Collatz sequence starting with `ans` |

- You can store and use your own variables:

| Input | Notes |
| ---------- | ----- |
| `a = b = c = 9` | assignments can be chained |
| `(a = 3)a(b = 5)bb` | not sure why you would ever do this, but it's `1125` |
| `a^bc^d` | evaluates as `a^(b*(c^d))`, unless `bc` exists, in which case it would be `a^(bc^d)` |
| `pi = 3.14; r = 3` | `pi` and `e` are (re)defineable. Use `del` to reset |
| `pir^2` | evaluated as `pi∙r^2`, unless a variable `pir` also exists, in which case it would be `(pir)^2` |
| `a = b = c = ab = bc = ac = abc = 1; abc` | multiple possible parses will trigger a warning |

- You can define your own functions. Use `vars` to see some preset functions.

| Input | Notes |
| ---------- | ----- |
| `square(x) = x^2` | simple square function! |
| `quad(a, b, c) = ((-b - sqrt(b^2 - 4ac))/2a, (-b + sqrt(b^2 - 4ac))/2a)` | quadratic solver |
| `hero(a, b, c) = sqrt((a + b + c)(a + b - c)(b + c - a)(c + a - b)/16)` | Hero's formula for area of triangles |
| `g(x) = x > 3 && x^2 \|\| x <= 3 && 2x` | domains can be declared using booleans and logical and/or |
| `h = gff` | composite functions are supported |
| `h = f^2g^3` | declares h(x) = ffggg(x) |
| `dot((x1, y1, z1), (x2, y2, z2)) = x1x2 + y1y2 + z1z2` | multiple parameters are supported |
| `cross((a, b, c), (d, e, f)) = (bf-ce, cd-af, ae-bd)` | tuples are supported, even as parameters |
| `sigma(f, l, u) = l <= u && f(l) + sigma(f, l+1, u) \|\| f(l)` | recursive functions are supported |
| `luhn(n, q = 1) = d = n % 10; n ? (q ? d : 2d > 9 ? 2d - 9 : 2d) + luhn(n // 10, 1 - q) : 0` | Luhn algorithm to calculate checksum |
| `collatz(n) = n > 1 && 1 + (n % 2 && collatz(3n + 1) \|\| collatz(n/2))` | Collatz number-of-steps-to-reach-1 |
| `collatz(n) = n > 1 ? 1 + (n % 2 ? collatz(3n + 1) : collatz(n/2)) : 0` | Alternative of above, using ternaries |
| `(1 + i)(2 - 3i)` | Complex numbers are fully implemented |
| `a = 2e^(ipi/4); b = i^i^i; c = sin(i)` | Try some fun complex calculations |

- Tuples have their own operators:

| Operator | Explanation |
| ---------- | ----- |
| `<+>` | Concatenation, e.g. `arr1 <+> arr2` |
| `@` | Indexing, e.g. `arr1 @ 1` |
| `$` | Length operator, e.g. `arr$` |
| `</` and `/>` | Left and Right knife operators (for slicing!) |
| `2 </ (1, 2, 3, 4, 5)` | Outward knife: Removes 2 elements from the left -> `(3, 4, 5)` |
| `2 /> (1, 2, 3, 4, 5)` | Inward knife: Keeps the 2 elements from the left -> `(1, 2)` |
| `(1, 2, 3, 4, 5) /> 2` | Outward knife: Removes 2 elements from the right -> `(1, 2, 3)` |
| `(1, 2, 3, 4, 5) </ 2` | Inward knife: Keeps 2 elements from the right -> `(4, 5)` |
| `1 </ (1, 2, 3, 4, 5) /> 1` | Outward knives on left and right: Removes first and last element -> `(2, 3, 4)` |

- As you may have noticed, this calculator is heavily influenced by Haskell.
- Here are examples of functions written in a "functional" style:

| Input | Notes |
| ---------- | ----- |
| `map(f, v) = v$ ? (f(v @ 0):) <+> map(f, 1 </ v) : ()` | map function |
| `map(x => x^2)` | a function which squares all elements in a list |
| `map(x => x^2)(range(5))` | `[0, 1, 4, 9, 16]` |
| `reduce(f, v, a) = v$ ? reduce(f, 1 </ v, f(a, v @ 0)) : a` | reduce function |
| `dotProduct(u, v) = u$ ? u @ 0 conj(v @ 0) + dotProduct(1 </ u, 1 </ v) : 0` | improved vector dot-product (any dimension) |
| `transpose(m, result = (), col = (), r = 0, c = 0) = result$ == (m @ 0)$ ? result : r == m$ ? transpose(m, result <+> (col:), (), 0, c + 1) : transpose(m, result, col <+> (m @ r @ c:), r + 1, c)` | matrix transposition |
| `matrixMult(A, B) = B = transpose(B); (helper(result = (), row = (), r = 0, c = 0) = r == A$ ? result : c == B$ ? helper(result <+> (row:), (), r + 1, 0) : helper(result, row <+> (dotProduct(A @ r, B @ c):), r, c + 1))()` | matrix multiplication. Observe that `helper` is an IIFE. |
| `euler(grad, (x, y), endX, stepSize, thisGrad = grad(x, y), thisRow = ((x, y, thisGrad):)) = x >= endX ? thisRow : thisRow <+> euler(grad, (x + stepSize, y + thisGrad * stepSize), endX, stepSize)` | Euler's method |

Update (v3.5.0) Lambda functions are now available

| Input | Notes |
| ---------- | ----- |
| `square = x => x^2` | another way to define a square function |
| `(x => x^2)(5)` | immediately invoked square function |
| `map = f => v => v$ ? (f(v @ 0):) <+> map(f)(1 </ v) : ()` | curried map function |
| `reduce = f => (v, a = 0) = v$ ? reduce(f)(1 </ v, f(a, v @ 0)) : a` | curried reduce function |

-----------
## List of currently supported math operators/functions:

| Type | Operator |
| ---------- | ----- |
| Arithmetic | `+`, `-`, `*`, `/`, `%`, `^`, `sqrt` |
| Combinatoric | `P`, `C`, `!` |
| Trigonometric | `sin`, `cos`, `tan`, `sec`, `cosec\|csc`, `cot` |
| Inverse Trig | `a[rc]sin`, `a[rc]cos`, `a[rc]tan` |
| Hyperbolic | `sinh`, `cosh`, `tanh` |
| Logarithmic | `ln`, `lg` |
| Logical | `&&`, `\|\|` |
| Equality | `==`, `!=` |
| Relational | `<`, `<=`, `>`, `>=` |
| Ternary | `<expression> ? <trueVal> : <falseVal>` |
| Complex | `abs`, `arg`, `conj`, `Re`, `Im` |
| Tuple manipulaton | `<+>`, `@`, `$`, `</`, `/>` (see above) |
| Vector dot and cross product | `.`, `><` |
| Lambda functions | `=>` |
