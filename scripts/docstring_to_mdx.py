#!/usr/bin/env python3
import re
import inspect
from typing import Any
from sphinx.ext.napoleon import Config, NumpyDocstring


def docstring_to_markdown(
    obj_name: str, obj: Any, module_path: str, config: dict = None
) -> str:
    """
    Convert a Python object's docstring to Markdown format via RST.

    Parameters
    ----------
    obj_name : str
        Name of the object (function, class, method)
    obj : Any
        The Python object itself
    module_path : str
        Import path to the module
    config : dict, optional
        Documentation configuration options

    Returns
    -------
    str
        Markdown representation of the docstring
    """
    # Initialize config if None
    if config is None:
        config = {}

    # Get the docstring
    docstring = inspect.getdoc(obj)

    # Get the main package name (first part of module_path)
    main_package_name = module_path.split(".")[0] if module_path else None

    # Determine object type for better RST conversion
    obj_type = "function"
    if inspect.isclass(obj):
        obj_type = "class"
    elif inspect.ismodule(obj):
        obj_type = "module"

    # Skip docstrings from built-in or external modules
    if obj_type == "class":
        # Get the actual module of this class, check if it's from our main package
        class_module = getattr(obj, "__module__", "")
        if not class_module.startswith(main_package_name):
            return f"# {obj_name}\n\n*Class imported from external module `{class_module}`.*"

        # Check if the docstring is inherited from any parent class
        for cls in obj.__mro__[1:]:  # Skip first (self) in MRO
            # Debug: Print each class in the MRO and its docstring source
            cls_doc = inspect.getdoc(cls)

            # Check if the parent class is from an external module
            cls_module = getattr(cls, "__module__", "")
            cls_is_external = not cls_module.startswith(main_package_name)

            # If this class's docstring matches our object's docstring,
            # it means our object is inheriting the docstring
            if cls_doc == docstring:
                print(
                    f"  Found inherited docstring from: {cls.__module__}.{cls.__name__}"
                )
                # For any other inherited docstring, replace with generic message
                if cls_is_external:
                    docstring = f"A {obj_type} inheriting from external class {cls.__module__}.{cls.__name__}."
                else:
                    docstring = (
                        f"A {obj_type} inheriting from {cls.__module__}.{cls.__name__}."
                    )
                print(f"  Replaced with: {docstring}")
                break

    if not docstring:
        return f"# {obj_name}\n\nNo documentation available."

    # Build header for Markdown output
    markdown = ["---", "sidebar_position: 2", "---", "", f"# {obj_name}", ""]

    # Add import path
    if module_path:
        markdown.append(f"*Defined in `{module_path}.{obj_name}`*\n")

    try:
        # Get signature for functions and classes
        if not inspect.ismodule(obj):
            try:
                signature = str(inspect.signature(obj))
                markdown.append(f"```python\n{obj_name}{signature}\n```\n")
            except (ValueError, TypeError):
                # Some objects might not have a signature
                pass

        # Convert docstring to RST, then to Markdown
        mdx_content = docstring_to_mdx(docstring, obj_type)

        # First extract the short description (first paragraph)
        first_paragraph_match = re.match(
            r"^(.*?)(?=\n\n|$)", mdx_content.strip(), re.DOTALL
        )
        first_paragraph = (
            first_paragraph_match.group(0) if first_paragraph_match else ""
        )

        # Remove the first paragraph from the content
        if first_paragraph:
            remaining_content = mdx_content[len(first_paragraph) :].strip()
            # Add the first paragraph outside the collapsible area
            markdown.append(first_paragraph)

            # Add the rest of the content in a collapsible section
            if remaining_content:
                markdown.append(
                    create_container_block(
                        "See detailed documentation",
                        remaining_content,
                        icon="📑",
                        is_open=True,
                    )
                )
        else:
            # If we can't parse out a first paragraph, just add everything to collapsible
            markdown.append(
                create_container_block(
                    "See detailed documentation",
                    mdx_content,
                    icon="📑",
                    is_open=True,
                )
            )

        # If it's a class, also document its class attributes, properties, and methods
        if inspect.isclass(obj):
            # Document class attributes first (if any)
            class_attributes = []

            # Helper function to check if an attribute belongs to the current class or has been defined in the main package
            def is_attribute_from_main_package(attr_name, attr_value):
                """
                Check if an attribute belongs to the current class or has been defined in the main package.

                Parameters
                ----------
                attr_name : str
                    Name of the attribute
                attr_value : Any
                    Value of the attribute

                Returns
                -------
                bool
                    True if attribute should be included, False otherwise
                """
                # Get built-in methods to skip from config, or use defaults
                skip_builtin_methods = config.get(
                    "skip_builtin_methods",
                    [
                        "from_bytes",
                        "to_bytes",
                        "__format__",
                        "__reduce__",
                        "__reduce_ex__",
                        "__subclasshook__",
                        "__init_subclass__",
                        "__dir__",
                        "__sizeof__",
                    ],
                )

                # Skip common built-in methods
                if attr_name in skip_builtin_methods:
                    # Check if it's a built-in method
                    if type(attr_value).__name__ in [
                        "builtin_function_or_method",
                        "method_descriptor",
                        "wrapper_descriptor",
                    ]:
                        return False

                # Check if attribute is directly defined in this class's __dict__ (not inherited)
                if attr_name in obj.__dict__:
                    return True

                # Special handling for enum members - always include them
                if hasattr(obj, "__members__") and attr_name in getattr(
                    obj, "__members__", {}
                ):
                    return True

                # For properties, check if the property getter is defined in this class or the main package
                if isinstance(attr_value, property) and attr_value.fget:
                    prop_module = getattr(attr_value.fget, "__module__", "")
                    # Handle None module names (could happen with dynamically created properties)
                    return (
                        prop_module is None
                        or prop_module == ""
                        or prop_module.startswith(main_package_name)
                    )

                # For other attributes, try to find where they're defined
                # Check for descriptor objects that might have a __module__ attribute
                if hasattr(attr_value, "__module__"):
                    attr_module = getattr(attr_value, "__module__", "")
                    # Handle None module names safely
                    return (
                        attr_module is None
                        or attr_module == ""
                        or attr_module.startswith(main_package_name)
                    )

                # Check all classes in MRO to see where this attribute is defined
                for cls in obj.__mro__:
                    if attr_name in cls.__dict__:
                        cls_module = getattr(cls, "__module__", "")
                        # Handle None module names safely
                        return (
                            cls_module is None
                            or cls_module == ""
                            or cls_module.startswith(main_package_name)
                        )

                # If we can't determine, be conservative and include it
                return True

            # Get all class variables and properties
            # Look at class annotations first (for type hints)
            class_annotations = getattr(obj, "__annotations__", {})
            for attr_name, attr_type in class_annotations.items():
                # Skip private attributes
                if attr_name.startswith("_"):
                    continue

                # Try to get the default value if available
                try:
                    attr_value = getattr(obj, attr_name, None)
                    # Don't include method objects
                    if inspect.isfunction(attr_value) or inspect.ismethod(attr_value):
                        continue

                    # Only include if it's from the main package
                    if is_attribute_from_main_package(attr_name, attr_value):
                        class_attributes.append((attr_name, attr_type, attr_value))
                except Exception:
                    # If we can't get the value, just include the name and type if it's in __annotations__
                    # since that's defined in the class directly
                    class_attributes.append((attr_name, attr_type, None))

            # Look for pydantic Field attributes which might not be in annotations
            # This captures fields defined with pydantic's Field class
            for attr_name, attr_value in obj.__dict__.items():
                if attr_name.startswith("_"):
                    continue

                # If already captured from annotations, skip
                if any(a[0] == attr_name for a in class_attributes):
                    continue

                # Check for pydantic Field objects
                if (
                    hasattr(attr_value, "__class__")
                    and attr_value.__class__.__name__ == "Field"
                ):
                    class_attributes.append(
                        (
                            attr_name,
                            getattr(attr_value, "annotation", "Any"),
                            attr_value,
                        )
                    )

            # Try to find other class variables and properties
            for attr_name in dir(obj):
                # Skip private attributes and already documented ones
                if attr_name.startswith("_") or any(
                    a[0] == attr_name for a in class_attributes
                ):
                    continue

                # Skip methods and inherited methods
                attr_value = getattr(obj, attr_name, None)
                if inspect.isfunction(attr_value) or inspect.ismethod(attr_value):
                    continue

                # Skip common magic methods and built-ins
                if attr_name in {
                    "__module__",
                    "__doc__",
                    "__dict__",
                    "__weakref__",
                    "__annotations__",
                }:
                    continue

                # Check if this is a property
                is_property = isinstance(attr_value, property)

                # Only add attributes that belong to our package
                if is_attribute_from_main_package(attr_name, attr_value):
                    # Add to our list if it's a property or a class attribute
                    if is_property:
                        # For properties, use the return type annotation if available
                        if (
                            hasattr(attr_value.fget, "__annotations__")
                            and "return" in attr_value.fget.__annotations__
                        ):
                            attr_type = attr_value.fget.__annotations__["return"]
                            # Store the actual property docstring, not just a marker
                            if attr_value.__doc__:
                                class_attributes.append(
                                    (attr_name, attr_type, attr_value)
                                )
                            else:
                                class_attributes.append(
                                    (attr_name, attr_type, "(property)")
                                )
                        else:
                            # Even without return type annotation, store the property object if it has docstring
                            if attr_value.__doc__:
                                class_attributes.append((attr_name, "Any", attr_value))
                            else:
                                class_attributes.append(
                                    (attr_name, "Any", "(property)")
                                )
                    elif not inspect.isfunction(attr_value) and not inspect.isclass(
                        attr_value
                    ):
                        # Skip if it's a function or a nested class
                        class_attributes.append(
                            (attr_name, type(attr_value).__name__, attr_value)
                        )

            # If we found any attributes, document them using the format_class_attributes function
            if class_attributes:
                markdown.append("\n")
                markdown.append(format_class_attributes(class_attributes))

            # Determine if we should include inherited methods
            include_inherited = config.get("include_inherited_docs", True)

            # List to store all methods we find (both direct and inherited)
            all_methods = []
            documented_methods = set()

            if include_inherited:
                # Get the Method Resolution Order (MRO) - the inheritance hierarchy
                for cls in obj.__mro__:
                    # Skip object itself (last in MRO)
                    if cls is object:
                        continue

                    # Skip classes not in our package
                    cls_module = cls.__module__
                    if not cls_module.startswith(main_package_name):
                        # Skip methods from external packages
                        print(
                            f"  Skipping methods from external class: {cls.__module__}.{cls.__name__}"
                        )
                        continue

                    # Skip classes based on patterns in skip_classes configuration
                    skip_class = False
                    for skip_pattern in config.get("skip_classes", []):
                        if re.match(
                            skip_pattern, f"{cls_module}.{cls.__name__}"
                        ) or re.match(skip_pattern, cls.__name__):
                            skip_class = True
                            print(
                                f"  Skipping methods from class: {cls.__module__}.{cls.__name__} (matched pattern: {skip_pattern})"
                            )
                            break

                    if skip_class:
                        continue

                    # Get methods from this class that are defined in this class's module
                    class_methods = []
                    for method_name, method in inspect.getmembers(
                        cls, predicate=inspect.isfunction
                    ):
                        # Skip private methods
                        if method_name.startswith("_"):
                            continue

                        # Skip already documented methods
                        if method_name in documented_methods:
                            continue

                        # Skip methods from external modules
                        method_module = getattr(method, "__module__", "")
                        if not method_module.startswith(main_package_name):
                            continue

                        # Add method to our list with source class info
                        source_cls = cls.__name__
                        is_inherited = cls is not obj

                        # For inherited methods, create a tuple with source info
                        if is_inherited:
                            class_methods.append((method_name, (method, source_cls)))
                        else:
                            class_methods.append((method_name, method))

                        documented_methods.add(method_name)

                    # Add methods from this class to the overall list
                    all_methods.extend(class_methods)
            else:
                # If not including inherited methods, just get the direct methods
                for method_name, method in inspect.getmembers(
                    obj, predicate=inspect.isfunction
                ):
                    if method_name.startswith("_"):
                        continue

                    # Skip methods from external modules
                    method_module = getattr(method, "__module__", "")
                    if not method_module.startswith(main_package_name):
                        continue

                    if method.__module__ == obj.__module__:
                        all_methods.append((method_name, method))

            # Now document all the methods we found
            for item in all_methods:
                method_name = item[0]

                # Skip methods that start with underscore (private methods)
                if method_name.startswith("_"):
                    continue

                # Handle case where method might be a tuple with source info
                if isinstance(item[1], tuple):
                    method, source_class = item[1]
                    is_inherited = True
                    source_module = method.__module__
                else:
                    method = item[1]
                    source_class = obj.__name__
                    source_module = method.__module__
                    is_inherited = False

                markdown.append(f"\n---\n\n## {obj_name}.{method_name}\n")

                # If the method is inherited, note where it comes from
                if is_inherited:
                    markdown.append(
                        f"*Inherited from `{source_module}.{source_class}`*\n"
                    )

                # Add method signature
                try:
                    signature = str(inspect.signature(method))
                    markdown.append(f"```python\n{method_name}{signature}\n```\n")
                except (ValueError, TypeError):
                    pass

                method_doc = inspect.getdoc(method)
                if method_doc:
                    try:
                        # Convert method docstring to RST, then to Markdown
                        method_rst = docstring_to_rst(method_doc, "method")
                        method_md = rst_to_mdx(method_rst)

                        # Apply the same first paragraph extraction/collapsible approach for methods
                        method_first_para = re.match(
                            r"^(.*?)(?=\n\n|$)", method_md.strip(), re.DOTALL
                        )
                        method_first_para = (
                            method_first_para.group(0) if method_first_para else ""
                        )

                        if method_first_para:
                            method_remaining = method_md[
                                len(method_first_para) :
                            ].strip()
                            markdown.append(method_first_para)
                            if method_remaining:
                                markdown.append(
                                    create_container_block(
                                        "See detailed documentation",
                                        method_remaining,
                                        icon="📑",
                                        is_open=True,
                                    )
                                )
                        else:
                            markdown.append(
                                create_container_block(
                                    "See detailed documentation",
                                    method_md,
                                    icon="📑",
                                    is_open=True,
                                )
                            )

                    except Exception as e:
                        markdown.append(
                            f"\n{method_doc}\n\n*Note: Raw docstring shown due to parsing issue: {str(e)}*"
                        )
                else:
                    markdown.append("\nNo documentation available for this method.")

    except Exception as e:
        # If conversion fails, use the raw docstring
        markdown.append(f"\n{docstring}")
        markdown.append(
            f"\n\n*Note: Raw docstring shown due to conversion issue: {str(e)}*"
        )

    return "\n".join(markdown)


def docstring_to_mdx(docstring, obj_type="function"):
    """
    Convert a NumPy-style docstring to MDX format.

    Parameters
    ----------
    docstring : str
        The docstring to convert
    obj_type : str
        The type of object ('function', 'class', 'module')

    Returns
    -------
    str
        Markdown content
    """
    rst_content = docstring_to_rst(docstring, obj_type)
    mdx_content = rst_to_mdx(rst_content)
    return mdx_content


def docstring_to_rst(docstring, obj_type="function"):
    """
    Convert a NumPy-style docstring to RST format using sphinx.ext.napoleon.

    Parameters
    ----------
    docstring : str
        The docstring to convert
    obj_type : str
        The type of object ('function', 'class', 'module')

    Returns
    -------
    str
        RST formatted docstring
    """
    if not docstring:
        return ""

    # Configure Napoleon
    config = Config(
        napoleon_use_param=True,
        napoleon_use_rtype=True,
        napoleon_use_admonition_for_examples=True,
        napoleon_use_admonition_for_notes=True,
        napoleon_use_admonition_for_references=True,
    )

    # Convert to RST using napoleon
    rst = NumpyDocstring(docstring, config)
    return str(rst)


def rst_to_mdx(rst_text):
    """
    Convert RST to Markdown using simple conversion method.

    Parameters
    ----------
    rst_text : str
        RST content to convert

    Returns
    -------
    str
        Markdown content
    """
    # Directly use simple_rst_to_markdown without trying other methods
    return simple_rst_to_markdown(rst_text)


def simple_rst_to_markdown(rst_text):
    """
    Simplified conversion of RST to Markdown for fallback.

    Parameters
    ----------
    rst_text : str
        RST content to convert

    Returns
    -------
    str
        Basic Markdown conversion

    See Also
    --------
    - https://www.sphinx-doc.org/en/master/usage/restructuredtext/directives.html
    - https://squidfunk.github.io/mkdocs-material/reference/admonitions/
    - https://docusaurus.io/docs/markdown-features/admonitions
    - https://github.com/refinedev/refine/blob/9d1e67d2fdde7c3dcddb9416afc8eb0bdce7a197/documentation/src/refine-theme/common-admonition.tsx#L141
    """
    if not rst_text:
        return ""

    md_text = rst_text

    # First, process all admonition directives

    # Process `Examples` admonitions (.. admonition:: Examples)
    md_text = re.sub(
        r".. admonition:: Examples\s*\n\n(.*?)(?=\n\n(?:\.\.|[^\s])|$)",
        lambda m: format_examples_section(m.group(1)),
        md_text,
        flags=re.DOTALL,
    )

    # Process `See also` admonitions (.. admonition:: See Also)
    md_text = re.sub(
        r".. admonition:: See Also\s*\n\n(.*?)(?=\n\n(?:\.\.|[^\s])|$)",
        lambda m: format_section_block(
            "See Also", format_references_content(m.group(1).strip()), collapsible=False
        ),
        md_text,
        flags=re.DOTALL,
    )

    # Process `See also` admonitions (.. seealso::)
    md_text = re.sub(
        r".. seealso::\s*(.*?)(?=\n\n(?:\.\.|[^\s])|$)",
        lambda m: format_section_block(
            "See Also", format_references_content(m.group(1).strip()), collapsible=False
        ),
        md_text,
        flags=re.DOTALL,
    )

    # Process `References` admonitions (.. admonition:: References)
    md_text = re.sub(
        r".. admonition:: References\s*\n\n(.*?)(?=\n\n(?:\.\.|[^\s])|$)",
        lambda m: format_section_block(
            "References",
            format_references_content(m.group(1).strip()),
            collapsible=False,
        ),
        md_text,
        flags=re.DOTALL,
    )

    # Process `Notes` admonitions (.. admonition:: Notes)
    md_text = re.sub(
        r".. admonition:: Notes\s*\n\n(.*?)(?=\n\n(?:\.\.|[^\s])|$)",
        lambda m: format_section_block("Notes", m.group(1).strip(), collapsible=False),
        md_text,
        flags=re.DOTALL,
    )

    # Process `note` admonitions (.. note::)
    md_text = re.sub(
        r".. note::\s*(.*?)(?=\n\n(?:\.\.|[^\s])|$)",
        lambda m: format_section_block("Notes", m.group(1).strip(), collapsible=False),
        md_text,
        flags=re.DOTALL,
    )

    # Process `warning` admonitions (.. warning::)
    md_text = re.sub(
        r".. warning::\s*(.*?)(?=\n\n(?:\.\.|[^\s])|$)",
        lambda m: format_section_block(
            "Warning", m.group(1).strip(), collapsible=False
        ),
        md_text,
        flags=re.DOTALL,
    )

    # Process other generic admonitions (.. admonition:: Title)
    md_text = re.sub(
        r".. admonition:: (.*?)\n\n(.*?)(?=\n\n(?:\.\.|[^\s])|$)",
        lambda m: format_section_block(
            m.group(1), m.group(2).strip(), collapsible=False
        ),
        md_text,
        flags=re.DOTALL,
    )

    # Process parameters - fixed escape sequences with raw strings (r prefix)
    parameters_section = format_parameters_section(md_text)
    if parameters_section:
        # Replace parameter blocks with the formatted table
        md_text = re.sub(
            r":param .*?(?=\n\n|$)", parameters_section, md_text, flags=re.DOTALL
        )

        # Remove type blocks
        md_text = re.sub(r":type .*?(?=\n\n|$)", "", md_text, re.DOTALL)

    # Process returns - fixed escape sequences
    returns_section = format_returns_section(md_text)
    if returns_section:
        # Replace returns blocks with the formatted table
        md_text = re.sub(
            r":returns?:.*?(?=\n\n|$)", returns_section, md_text, flags=re.DOTALL
        )

        # Remove rtype block
        md_text = re.sub(r":rtype:.*?(?=\n\n|$)", "", md_text, re.DOTALL)

    # Handle sections
    md_text = re.sub(r"([^\n]+)\n-{3,}", r"## \1", md_text)

    # Process math - fixed escape sequence
    md_text = re.sub(
        r".. math::(.*?)(?=\n\n|$)",
        lambda m: f"\n$$\n{m.group(1).strip()}\n$$\n",
        md_text,
        flags=re.DOTALL,
    )

    # Process inline math
    md_text = re.sub(r":math:`(.*?)`", r"$\1$", md_text)

    # Process other inline roles
    md_text = re.sub(r":(class|func|mod|obj|ref|meth|attr):`(.*?)`", r"`\2`", md_text)

    formatted_md_text = escape_for_all_except_code_blocks(md_text)

    return formatted_md_text


def escape_for_all_except_code_blocks(md_text):
    """ """
    # Apply escape_for_mdx to all text, but preserve code blocks
    # First, extract and save all code blocks
    code_blocks = []

    def save_code_block(match):
        code_blocks.append(match.group(1))
        return f"CODE_BLOCK_PLACEHOLDER_{len(code_blocks) - 1}"

    # Extract all code blocks (```...```)
    md_text_with_placeholders = re.sub(
        r"```[^\n]*\n(.*?)```", save_code_block, md_text, flags=re.DOTALL
    )

    # Apply escape_for_mdx to the text (excluding code blocks)
    escaped_text = escape_for_mdx(md_text_with_placeholders)

    # Restore code blocks
    def restore_code_block(match):
        index = int(match.group(1))
        return f"```\n{code_blocks[index]}```"

    final_text = re.sub(
        r"CODE_BLOCK_PLACEHOLDER_(\d+)", restore_code_block, escaped_text
    )

    return final_text


def escape_for_mdx(text):
    """
    Escape special characters in text to make it safe for MDX rendering.

    Parameters
    ----------
    text : str
        Text to escape
    escape_quotes : bool, default False
        Whether to escape single quotes

    Returns
    -------
    str
        MDX-safe
    """
    if not text:
        return ""

    # Replace colons with HTML entities in code contexts
    # This is particularly important in parameter type definitions
    text = re.sub(r"`([^`]*):([^`]*)`", r"`\1&#58;\2`", text)

    # Replace colons in default values and other potentially problematic contexts
    text = re.sub(
        r"(default|optional)([^,\.]*):([^,\.]*)([,\.])",
        r"\1\2&#58;\3\4",
        text,
        flags=re.IGNORECASE,
    )

    # Handle JSX/HTML element-like patterns with colons
    text = re.sub(r"<([a-zA-Z0-9_]+):([^>]+)>", r"<\1_\2>", text)

    # Escape other potential MDX parsing issues
    # Handle curly braces which can be interpreted as JSX expressions
    text = text.replace("{", "&#123;").replace("}", "&#125;")

    return text


def format_parameters_section(params_content):
    """
    Format parameters section as a Markdown table.

    Parameters
    ----------
    params_content : str
        Raw parameters content from docstring

    Returns
    -------
    str
        Formatted parameters table in Markdown
    """
    param_blocks = re.findall(
        r":param (\w+): (.*?)(?=:param|:type|:returns|:rtype|$)",
        params_content,
        re.DOTALL,
    )
    if not param_blocks:
        return ""

    param_table = "## Parameters\n\n| Name | Type | Description | Default |\n|------|------|-------------|--------|\n"

    for name, desc in param_blocks:
        # Find matching type
        type_match = re.search(
            rf":type {name}: (.*?)(?=:param|:type|:returns|:rtype|$)",
            params_content,
            re.DOTALL,
        )
        type_str = type_match.group(1).strip() if type_match else ""

        # Escape pipe characters in type annotations to prevent them from breaking the Markdown table
        # Replace | with the \| in type strings
        if "|" in type_str:
            type_str = type_str.replace("|", r"\|")

        # Check for default/optional
        is_optional = "optional" in type_str.lower()
        default = "Optional" if is_optional else "*Required*"

        # Extract explicit default value
        default_match = re.search(
            r"[Dd]efault(?:s)?(?: is| are| value is)? *[=:]? *(.+?)\.?$", desc
        )
        if default_match:
            default = default_match.group(1).strip()

        # Clean description and format multi-line descriptions for table compatibility
        desc = desc.strip()

        # Make multi-line descriptions work in table cells by replacing newlines with <br/>
        # Also handle bullet points/lists - use self-closing tags
        formatted_desc = []
        for line in desc.split("\n"):
            line = line.strip()
            if line.startswith("-") or line.startswith("*"):
                # Format list items with HTML (using self-closing tags)
                formatted_desc.append(f"<br/>• {line[1:].strip()}")
            else:
                formatted_desc.append(line)

        # Join lines with space or <br/> for proper table formatting in MDX
        desc = " ".join(formatted_desc).replace("<br/> ", "<br/>")

        param_table += f"| **{name}** | `{type_str}` | {desc} | {default} |\n"

    return param_table


def format_class_attributes(class_attributes):
    """
    Format class attributes as a Markdown table.

    Parameters
    ----------
    class_attributes : list of tuples
        List of (attr_name, attr_type, attr_value) tuples representing class attributes

    Returns
    -------
    str
        Formatted Markdown table of class attributes
    """
    if not class_attributes:
        return ""

    attr_table = "## Class Attributes\n\n"
    attr_table += "| Name | Type | Description |\n"
    attr_table += "|------|------|-------------|\n"

    for attr_name, attr_type, attr_value in sorted(
        class_attributes, key=lambda x: x[0]
    ):
        # Format the type nicely
        if isinstance(attr_type, str):
            type_str = f"`{attr_type}`"
        else:
            try:
                # Get the name of the type
                type_str = f"`{attr_type.__name__}`"
            except AttributeError:
                try:
                    # Try using str representation instead
                    type_str = f"`{str(attr_type)}`"
                except Exception:
                    type_str = "`Unknown`"

        # Get the value (for enums and constants, otherwise empty)
        if attr_value == "(property)":
            value_str = "*Property*"
        elif attr_value is None:
            value_str = ""
        else:
            try:
                # Try to represent the value, but limit its size
                value_repr = repr(attr_value)
                if isinstance(attr_value, property):
                    value_str = "*Property*"
                else:
                    value_str = f"*Default:* `{value_repr}`"
            except Exception:
                value_str = ""

        # Extract property docstring
        desc = value_str

        # Handle property docstring
        if isinstance(attr_value, property) and attr_value.__doc__:
            # We have the actual property object with a docstring
            desc = attr_value.__doc__.strip()

        attr_table += f"| **{attr_name}** | {type_str} | {desc} |\n"

    return attr_table


def format_returns_section(returns_content):
    """
    Format returns section as a Markdown table.

    Parameters
    ----------
    returns_content : str
        Raw returns content from docstring

    Returns
    -------
    str
        Formatted returns table in Markdown
    """
    # Extract returns description and type
    returns_match = re.search(
        r":returns?: (.*?)(?=:rtype:|$)", returns_content, re.DOTALL
    )
    rtype_match = re.search(r":rtype: (.*?)(?=\n\n|$)", returns_content, re.DOTALL)

    if not returns_match:
        return ""

    returns_desc = returns_match.group(1).strip()
    rtype = rtype_match.group(1).strip() if rtype_match else ""

    # Format multi-line return descriptions with self-closing tags
    formatted_desc = []
    for line in returns_desc.split("\n"):
        line = line.strip()
        if line.startswith("-") or line.startswith("*"):
            # Format list items with HTML (using self-closing tags)
            formatted_desc.append(f"<br/>• {line[1:].strip()}")
        else:
            formatted_desc.append(line)

    # Join lines with space or <br/> for proper table formatting
    returns_desc = " ".join(formatted_desc).replace("<br/> ", "<br/>")

    returns_table = "## Returns\n\n| Type | Description |\n|------|-------------|\n"
    returns_table += f"| `{rtype}` | {returns_desc} |\n"

    return returns_table


def format_examples_section(examples_content):
    """
    Process Examples section content with an icon.

    Parameters
    ----------
    examples_content : str
        The content of the Examples section

    Returns
    -------
    str
        Formatted Examples section
    """
    # Format Python interactive examples with special style
    examples_content = format_interactive_examples(examples_content)
    # # Format code blocks properly
    # # This regex will handle >>> style Python interactive examples
    # examples_content = re.sub(
    #     r'>>> (.*?)(?=\n>>> |\n\n|$)',
    #     lambda m: f"```python\n>>> {m.group(1)}\n```",
    #     examples_content,
    #     flags=re.DOTALL
    # )

    # Make sure all code blocks are properly closed
    # Check if there are any unclosed code blocks
    open_blocks = examples_content.count("```") % 2
    if open_blocks:
        examples_content += "\n```"

    # Use the unified format_section_block function with collapsible=False
    return format_section_block("Examples", examples_content, collapsible=False)


def format_interactive_examples(content):
    """
    Format interactive Python examples with visible input and output sections,
    with prompts removed for easy copying.

    Parameters
    ----------
    content : str
        Raw examples content

    Returns
    -------
    str
        Formatted examples
    """
    if not content:
        return content

    # Identify code blocks with >>> prompts
    lines = content.split("\n")
    formatted_lines = []

    i = 0
    in_code_block = False

    while i < len(lines):
        line = lines[i]

        # Check if this is the start of a code block with >>> prompt
        if re.match(r"^\s*>>>.*", line) and not in_code_block:
            in_code_block = True

            # Store both the original lines (with prompts) and clean lines (without prompts)
            orig_lines = []
            clean_lines = []

            # Add all lines that are part of this input block (>>> or ...)
            while i < len(lines) and (
                re.match(r"^\s*>>>.*", lines[i]) or re.match(r"^\s*\.\.\..*", lines[i])
            ):
                # Keep track of original line (with prompt)
                orig_lines.append(lines[i])

                # Create a clean version without the prompt
                if re.match(r"^\s*>>>(.*)$", lines[i]):
                    clean_line = re.sub(r"^\s*>>>(.*)$", r"\1", lines[i])
                else:
                    clean_line = re.sub(r"^\s*\.\.\.(.*)$", r"\1", lines[i])

                clean_lines.append(clean_line)
                i += 1

            # Start of Python input block - showing code without prompts
            formatted_lines.append("```python")
            # Add clean lines (without prompts) to make copying easier
            formatted_lines.extend(clean_lines)
            formatted_lines.append("```")

            # Check if there's output following the input
            output_lines = []
            while (
                i < len(lines)
                and lines[i].strip()
                and not re.match(r"^\s*>>>.*", lines[i])
                and not re.match(r"^\s*\.\.\..*", lines[i])
            ):
                output_lines.append(lines[i])
                i += 1

            # If we have output, format it
            if output_lines:
                formatted_lines.append("**Out:**")
                formatted_lines.append("```")
                formatted_lines.extend(output_lines)
                formatted_lines.append("```")

            in_code_block = False
        else:
            # This is regular text or empty line
            formatted_lines.append(line)
            i += 1

    return "\n".join(formatted_lines)


def format_references_content(content):
    """
    Format reference content as a list.

    Parameters
    ----------
    content : str
        Raw references content

    Returns
    -------
    str
        Formatted references content as a list
    """
    # Split by lines and clean up
    lines = content.strip().split("\n")
    formatted_items = []

    for line in lines:
        line = line.strip()
        if line and (line.startswith("-") or line.startswith("*")):
            formatted_items.append(f"<br/>• {line[1:].strip()}")
        else:
            formatted_items.append(line)

    # Join all formatted items
    return "\n".join(formatted_items)


def _format_as_collapsible(section_name, content):
    """
    Format a section as a collapsible Markdown detail block with icon.

    Parameters
    ----------
    section_name : str
        Name of the section
    content : str
        Content to put inside the collapsible block

    Returns
    -------
    str
        Formatted collapsible block
    """
    # Use the unified format_section_block function with collapsible=True
    return format_section_block(section_name, content, collapsible=True)


def format_section_block(section_name, content, collapsible=False):
    """
    Format a section as either a collapsible admonition or a regular admonition.

    Parameters
    ----------
    section_name : str
        Name of the section
    content : str
        Content to put inside the block
    collapsible : bool, default=False
        Whether to make the admonition collapsible

    Returns
    -------
    str
        Formatted admonition in Markdown
    """
    if not content:
        return ""

    # Map section names to admonition types in Docusaurus
    admonition_map = {
        "Notes": "note",
        "Note": "note",
        "See Also": "info",
        "References": "info",
        "Examples": "tip",
        "Example": "tip",
        "Warning": "warning",
        "Warnings": "warning",
        "Caution": "danger",
        "Danger": "danger",
        "Important": "tip",
        "Tip": "tip",
        "Tips": "tip",
        "Info": "info",
        "Information": "info",
        "Parameters": "note",
        "Returns": "note",
        "Usage": "tip",
        "Implementation": "info",
        "Details": "info",
        "Algorithm": "info",
        "Error": "danger",
        "Errors": "danger",
        "Bug": "warning",
        "Bugs": "warning",
    }

    # Get the admonition type, default to "note"
    admonition_type = admonition_map.get(section_name, "note")

    # Check if content needs to be wrapped in a code block
    is_list = re.match(r"^- ", content.strip())
    has_code_blocks = "```" in content

    if not is_list and not has_code_blocks and not content.strip().startswith("```"):
        content = f"```\n{content}\n```"

    # Create admonition with optional collapsibility
    return create_admonition(
        admonition_type,
        content,
        title=section_name,
        is_open=True,
        collapsible=collapsible,
    )


def create_admonition(
    admonition_type, content, title=None, is_open=True, collapsible=False
):
    """
    Create a Docusaurus-style admonition with optional collapsibility.

    Parameters
    ----------
    admonition_type : str
        Type of admonition (note, info, tip, warning, danger, etc.)
    content : str
        Content inside the admonition
    title : str, optional
        Optional custom title. If None, uses the capitalized admonition type
    is_open : bool, default=True
        For collapsible admonitions, whether it's open by default
    collapsible : bool, default=False
        Whether to make the admonition content collapsible

    Returns
    -------
    str
        Formatted admonition in Markdown
    """
    # Map admonition types to supported Docusaurus types
    docusaurus_type_map = {
        # Standard Docusaurus admonition types
        "note": "note",
        "tip": "tip",
        "info": "info",
        "warning": "warning",
        "danger": "danger",
        # Map alternate types to the standard ones
        "caution": "danger",
        "failure": "danger",
        "important": "info",
        "see_also": "info",
        "references": "info",
        "examples": "tip",
        "notes": "note",
        "example": "tip",
        "success": "tip",
        "question": "info",
        "bug": "warning",
        "quote": "note",
    }

    # Map to official Docusaurus admonition type, default to "note"
    docusaurus_type = docusaurus_type_map.get(admonition_type.lower(), "note")

    # Titles mapping for common sections
    type_title_map = {
        "note": "Note",
        "tip": "Tip",
        "info": "Info",
        "warning": "Warning",
        "danger": "Danger",
        "caution": "Caution",
        "important": "Important",
        "see_also": "See Also",
        "references": "References",
        "examples": "Examples",
        "notes": "Notes",
        "example": "Example",
        "success": "Success",
        "question": "Question",
        "failure": "Failure",
        "bug": "Bug",
        "quote": "Quote",
    }

    # Use provided title or get default from map
    display_title = (
        title
        if title is not None
        else type_title_map.get(admonition_type.lower(), admonition_type.capitalize())
    )

    if collapsible:
        # For collapsible sections, use HTML details elements with admonition classes
        open_attr = " open" if is_open else ""
        return f"""<details{open_attr}>
<summary>{display_title}</summary>

{content}

</details>"""
    else:
        # Use standard Docusaurus admonition syntax
        return f":::{docusaurus_type}[{display_title}]\n\n{content}\n\n:::"


def create_container_block(summary_text, content, is_open=True, icon=None):
    """
    Create a container block styled as a Docusaurus admonition.

    Parameters
    ----------
    summary_text : str
        Text to display in the summary (clickable header)
    content : str
        Content to put inside the admonition
    is_open : bool, default=True
        Whether the admonition should be open by default
    icon : str, optional
        Optional icon to display before the summary text

    Returns
    -------
    str
        Formatted container block
    """
    if not content:
        return ""

    # Add icon if provided
    title = f"{icon} {summary_text}" if icon else summary_text

    # For "See detailed documentation" sections, use "info" admonition type
    if "detailed documentation" in summary_text.lower():
        admonition_type = "info"
    else:
        # For other section types, try to infer the appropriate type
        admonition_type = "note"  # default

        # Check for common keywords in the title to determine type
        title_lower = summary_text.lower()
        if any(word in title_lower for word in ["example", "usage", "how to"]):
            admonition_type = "tip"
        elif any(word in title_lower for word in ["warning", "caution", "important"]):
            admonition_type = "warning"
        elif any(word in title_lower for word in ["danger", "error", "critical"]):
            admonition_type = "danger"
        elif any(
            word in title_lower for word in ["info", "note", "see also", "references"]
        ):
            admonition_type = "info"

    return create_admonition(
        admonition_type, content, title=title, is_open=is_open, collapsible=True
    )
