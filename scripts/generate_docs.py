#!/usr/bin/env python3
"""
Script to convert Python docstrings to Markdown files.
Handles NumPy-style docstrings with comprehensive formatting.
"""

import sys
import inspect
import importlib
import pkgutil
import argparse
import json
import re
from pathlib import Path
from docstring_utils import docstring_to_markdown

def main():
    parser = argparse.ArgumentParser(description="Convert Python docstrings to Markdown files")
    parser.add_argument("source_dir", help="Source directory containing Python modules")
    parser.add_argument("output_dir", help="Output directory for Markdown files")
    parser.add_argument("--package", help="Base package name")
    parser.add_argument("--config", help="Path to documentation configuration JSON file", default=None)

    args = parser.parse_args()

    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Load configuration
    config = {
        "skip_modules": [],
        "skip_classes": [],
        "inherit_docs": True,
        "include_only_modules": [],
        "from_init": True,
        "sidebar_position": 4
    }
    
    if args.config and Path(args.config).exists():
        with open(args.config, 'r') as f:
            config.update(json.load(f))

    # Extract modules from __init__.py if requested
    init_modules = []
    allowed_classes = []
    class_modules = {}
    if config.get("from_init", True) and args.package:
        init_modules, allowed_classes, class_modules = extract_modules_from_init(args.package)
        if init_modules:
            print(f"Found {len(init_modules)} modules in __init__.py")
            print(f"Found {len(allowed_classes)} classes/functions in __all__: {allowed_classes}")
            # Override include_only_modules with modules found in __init__ if from_init is enabled
            config['include_only_modules'] = init_modules
            # Store the allowed class names in config
            config['allowed_classes'] = allowed_classes
            # Store the mapping of classes to their modules
            config['class_modules'] = class_modules

    # Get sidebar position from config - should be a number (already calculated in shell script if it was "last")
    sidebar_position = config.get("sidebar_position", 4)
    
    # Make sure sidebar_position is treated as an integer
    try:
        sidebar_position = int(sidebar_position)
    except (ValueError, TypeError):
        sidebar_position = 1
        print(f"Warning: Invalid sidebar_position value in config, using default: {sidebar_position}")
    
    # Create API index file
    with open(output_path / "index.md", "w") as f:
        f.write("""---
sidebar_position: 1
title: API Documentation
sidebar_label: Overview
---

# API Documentation

This section contains the automatically generated API documentation for all modules in the project.

The documentation is generated from NumPy-style docstrings in the Python source code using a custom script.

## Available Modules

Each module contains its own classes and functions. Browse the modules in the sidebar to explore the API documentation.

## How to Use This Documentation

Each module's documentation includes:

- **Functions** with their parameters, return values, examples, and notes
- **Classes** with their methods, properties, and usage examples

The documentation follows the NumPy docstring standard, which provides a consistent format for:

- Parameter descriptions with types
- Return value descriptions
- Examples showing usage
- Notes, warnings, and references

## Updating the Documentation

This documentation is automatically generated from the docstrings in the source code. To update it:

1. Update the docstrings in the Python code
2. Run the docstring conversion script
3. The changes will be reflected in the documentation

## Explore API Modules

import DocCardList from '@theme/DocCardList';

<DocCardList />
""")

    # Create category file for API root using the specified position
    create_category_file(
        output_path,
        "API Reference",
        sidebar_position,
        doc_id="api/index",
    )

    if args.package:
        # Process a specific package
        process_module(args.package, output_path, args.package, config=config)
    else:
        # Find all top-level modules in the source directory
        for path in Path(args.source_dir).glob("*.py"):
            if path.name != "__init__.py":
                module_name = path.stem
                process_module(module_name, output_path, config=config)

        # Find all packages (directories with __init__.py)
        for path in Path(args.source_dir).glob("*/__init__.py"):
            package_name = path.parent.name
            process_module(package_name, output_path, config=config)

    print(f"Documentation generated in {output_path}")

def extract_modules_from_init(package_name):
    """
    Extract modules explicitly imported in __init__.py of a package.
    Also extract class names that should be documented.
    
    Parameters
    ----------
    package_name : str
        The name of the package to inspect
        
    Returns
    -------
    tuple
        (List of module names, List of class names) found in __init__.py
    """
    try:
        # Import the package
        package = importlib.import_module(package_name)
        
        # Always include the base package itself
        modules = [package_name]
        class_names = []
        class_modules = {}  # Track which module contains each class
        
        # Get the __all__ variable, if defined
        if hasattr(package, '__all__'):
            # Get all classes and functions that should be documented
            class_names = package.__all__
            
            # Extract modules from __all__ items and map classes to their modules
            for name in package.__all__:
                if not name.startswith('_'):  # Skip private members
                    # Find the module containing this object
                    obj = getattr(package, name, None)
                    if obj is not None:
                        if inspect.ismodule(obj):
                            # If it's a module, add it directly
                            modules.append(obj.__name__)
                        else:
                            # If it's a class/function, get its module
                            module_name = getattr(obj, '__module__', None)
                            if module_name and module_name.startswith(package_name):
                                modules.append(module_name)
                                # Track which module contains this class
                                class_modules[name] = module_name
        
        # Also look at imported modules even if __all__ is defined
        for name, obj in inspect.getmembers(package):
            if not name.startswith('_'):  # Skip private members
                if inspect.ismodule(obj) and obj.__name__.startswith(package_name):
                    modules.append(obj.__name__)
                elif inspect.isclass(obj) or inspect.isfunction(obj):
                    module_name = obj.__module__
                    if module_name.startswith(package_name) and module_name != package_name:
                        modules.append(module_name)
                        # Add it to our class -> module mapping if it's in __all__
                        if name in class_names:
                            class_modules[name] = module_name
                    elif module_name == package_name:
                        # For objects in the base module, make sure the base module is included
                        if package_name not in modules:
                            modules.append(package_name)
                        
        print(f"Classes and their modules: {class_modules}")
        return list(set(modules)), class_names, class_modules  # Remove duplicates from modules
    except Exception as e:
        print(f"Error extracting modules from {package_name}.__init__: {str(e)}")
        return [package_name], [], {}

def should_process_module(module_name, config):
    """
    Check if a module should be processed based on configuration.
    
    Parameters
    ----------
    module_name : str
        The name of the module to check
    config : dict
        Configuration dictionary
        
    Returns
    -------
    bool
        True if module should be processed, False if it should be skipped
    """
    # Skip modules in the skip list
    for skip_pattern in config.get('skip_modules', []):
        if re.match(skip_pattern, module_name):
            print(f"Module '{module_name}' skipped by config: {skip_pattern}")
            return False
    
    # If there's an include_only list, only process modules in that list
    include_only = config.get('include_only_modules', [])
    if include_only:
        for include_pattern in include_only:
            if re.match(include_pattern, module_name):
                return True
        print(f"Module '{module_name}' not in include list: {include_only}")
        return False  # Not in include list
    
    # Default to processing if no include_only list
    return True

def process_module(module_name: str, output_dir: Path, package_name: str=None, config: dict=None) -> None:
    """
    Process a module and generate Markdown files for all its objects.

    Parameters
    ----------
    module_name : str
        Name of the module to process
    output_dir : Path
        Directory where Markdown files will be saved
    package_name : str, optional
        Parent package name, if the module is part of a package
    config : dict, optional
        Configuration dictionary for controlling which modules/classes to document
    """
    if config is None:
        config = {}
        
    # Check if we should process this module based on configuration
    if not should_process_module(module_name, config):
        print(f"Skipping module: {module_name} (filtered by config)")
        return
    
    print(f"Processing module: {module_name}")

    try:
        # Import the module
        module = importlib.import_module(module_name)
        
        # Get simple module name (last part after the dot)
        simple_module_name = module_name.split('.')[-1]
        
        # Determine main package name
        main_package_name = package_name if package_name else module_name.split('.')[0]

        # Get all the things we want to document
        functions = inspect.getmembers(module, inspect.isfunction)
        classes = inspect.getmembers(module, inspect.isclass)
        
        # Filter out functions that would be skipped
        documentable_functions = []
        for func_name, func in functions:
            if func_name.startswith('_') or func.__module__ != module.__name__:
                continue
            
            allowed_classes = config.get('allowed_classes', [])
            if allowed_classes and func_name not in allowed_classes:
                continue
                
            if not is_from_main_package(func, main_package_name):
                continue
                
            documentable_functions.append((func_name, func))
        
        # Filter out classes that would be skipped
        documentable_classes = []
        
        # First, check if this is the main package module and has classes from __all__
        class_modules = config.get('class_modules', {})
        is_main_package_module = module_name == main_package_name
        
        # If this is the main package module, try to import and document classes that are in __all__
        # but defined in submodules
        if is_main_package_module and class_modules:
            for class_name, class_module_name in class_modules.items():
                try:
                    # If the class is from a different module, get it from its original module
                    if class_module_name != module_name:
                        # Import the module that contains this class
                        try:
                            class_module = importlib.import_module(class_module_name)
                            if hasattr(class_module, class_name):
                                cls = getattr(class_module, class_name)
                                # Add the class with a note about its original module
                                print(f"  Including class {class_name} from module {class_module_name} in documentation")
                                documentable_classes.append((class_name, cls))
                        except ImportError:
                            print(f"  Could not import module {class_module_name} for class {class_name}")
                except Exception as e:
                    print(f"  Error processing class {class_name} from {class_module_name}: {str(e)}")
        
        # Process regular classes defined in this module
        for class_name, cls in classes:
            if cls.__module__ != module.__name__:
                continue
                
            if not is_from_main_package(cls, main_package_name):
                continue
            
            skip_class = False
            for skip_pattern in config.get('skip_classes', []):
                if re.match(skip_pattern, f"{module_name}.{class_name}") or re.match(skip_pattern, class_name):
                    skip_class = True
                    break
            
            allowed_classes = config.get('allowed_classes', [])
            if allowed_classes and class_name not in allowed_classes:
                skip_class = True
                
            if skip_class:
                continue
            
            documentable_classes.append((class_name, cls))
        
        # Check if module has any substantial documentation
        module_doc = inspect.getdoc(module)
        has_module_doc = module_doc and module_doc.strip() and module_doc != "Module documentation."
        
        # Check if module has __all__ attribute, which indicates important exports
        has_all = hasattr(module, '__all__') and len(module.__all__) > 0
        
        # Check if this is the main package module, which should always be documented
        is_main_package = module_name == main_package_name
        
        # Only skip if not the main package and has no content
        if not is_main_package and not has_all and not documentable_functions and not documentable_classes and not has_module_doc:
            print(f"  Skipping module {module_name}: No documentable content")
            return
        
        # If we reach this point, we're documenting something important
        if not documentable_functions and not documentable_classes and not has_module_doc:
            if is_main_package:
                print(f"  Documenting {module_name}: Main package module")
            elif has_all:
                print(f"  Documenting {module_name}: Has __all__ exports")

        # Create output directory for this module
        module_dir = output_dir / simple_module_name
        module_dir.mkdir(parents=True, exist_ok=True)

        # Document module itself - create an index.md file
        with open(module_dir / "index.md", "w") as f:
            content = ["---", "sidebar_position: 1", "---", "", f"# {simple_module_name}", ""]
            
            if module_doc:
                content.append(module_doc)
            else:
                content.append("Module documentation.")
            
            # If the module has an __all__ attribute, document what's exported
            if hasattr(module, '__all__') and len(module.__all__) > 0:
                content.append("\n## Exported Members\n")
                content.append("This module exports the following members:\n")
                for item in module.__all__:
                    content.append(f"- `{item}`")
            
            # Add DocCardList component at the end to show child pages
            content.append("\n## Module Contents\n")
            content.append("import DocCardList from '@theme/DocCardList';")
            content.append("")
            content.append("<DocCardList />")
                    
            f.write("\n".join(content))

        # Create category file for Docusaurus - point to the index.md file to avoid duplicate routes
        create_category_file(
            module_dir,
            f"{simple_module_name.replace('_', ' ').title()}",  # Convert snake_case to Title Case
            1,  # Position
            None,  # No description needed when using doc ID
            f"api/{simple_module_name}/index",  # Point to the index.md file
            False  # Not collapsed by default
        )

        position = 2  # Start position after index.md

        # Document functions - only those in __all__ if using --from-init
        for func_name, func in documentable_functions:
            # Generate documentation for the function
            markdown = docstring_to_markdown(func_name, func, module_name, config=config)
            
            # Update the position in the frontmatter
            markdown = markdown.replace("sidebar_position: 2", f"sidebar_position: {position}")
            position += 1

            with open(module_dir / f"function_{func_name}.md", "w") as f:
                f.write(markdown)

        # Document classes - only those in __all__ if using --from-init
        for class_name, cls in documentable_classes:
            # Generate documentation for the class with inherited docs from base classes
            class_config = {**config, 'include_inherited_docs': config.get('inherit_docs', True)}
            markdown = docstring_to_markdown(class_name, cls, module_name, config=class_config)
            
            # Update the position in the frontmatter
            markdown = markdown.replace("sidebar_position: 2", f"sidebar_position: {position}")
            position += 1

            with open(module_dir / f"class_{class_name}.md", "w") as f:
                f.write(markdown)

        # Look for submodules and process them too
        if hasattr(module, '__path__'):
            for _, submodule_name, is_pkg in pkgutil.iter_modules(module.__path__, module.__name__ + '.'):
                process_module(submodule_name, output_dir, main_package_name, config=config)

    except Exception as e:
        print(f"Error processing module {module_name}: {str(e)}")
        import traceback
        traceback.print_exc()

def create_category_file(dir_path, label, position, description=None, doc_id=None, collapsed=False):
    """
    Create a _category_.json file for Docusaurus sidebar customization.

    Parameters
    ----------
    dir_path : Path
        Directory where to create the category file
    label : str
        Display label for the category in the sidebar
    position : int
        Position in the sidebar (lower numbers appear first)
    description : str, optional
        Description to show on the generated index page
    doc_id : str, optional
        ID of a document to link to. If provided, clicking the category links to this doc.
        If not provided, a generated index page is created.
    collapsed : bool, optional
        Whether the category should be collapsed by default
    """
    category = {
        "label": label,
        "position": position,
        "collapsible": True,
        "collapsed": collapsed
    }

    # When doc_id is not provided or is explicitly set to None, use generated-index
    if doc_id is None:
        category["link"] = {
            "type": "generated-index"
        }
        if description:
            category["link"]["description"] = description
    else:
        # When doc_id is provided, use it
        category["link"] = {
            "type": "doc",
            "id": doc_id
        }

    # Write the category file
    with open(dir_path / "_category_.json", "w") as f:
        json.dump(category, f, indent=2)

def is_from_main_package(obj, main_package_name=None):
    """
    Check if an object (class or function) belongs to the main package.
    
    Parameters
    ----------
    obj : object
        The object to check
    main_package_name : str, optional
        The name of the main package
        
    Returns
    -------
    bool
        True if object belongs to main package, False if it's external
    """
    if main_package_name is None:
        return True  # If no main package specified, include everything
    
    # Get the module of the object
    obj_module = getattr(obj, '__module__', '')
    
    # Check if the module starts with the main package name
    return obj_module.startswith(main_package_name)

if __name__ == "__main__":
    main()