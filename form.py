import streamlit as st
import logging
import re
from dynamic_schema import DynamicGenSchema
from utils import profile_page_loader
from db import get_pydantic_models, update_pydantic_models,delete_pydantic_model
import time

logger = logging.getLogger(__name__)

profile_page_loader(logger=logger)


# def resolve_json_schema(json_schema: dict) -> Type[BaseModel]:
#     json_type_mapping = {
#         "string": str,
#         "number": float,
#         "integer": int,
#         "boolean": bool,
#         "object": dict,
#         "array": list,
#     }

#     defs = json_schema.get("$defs", {})
#     nested_models: Dict[str, Type[BaseModel]] = {}

#     def create_model_from_schema(sub_schema: dict, model_name: str) -> Type[BaseModel]:
#         properties = sub_schema.get("properties", {})
#         required = set(sub_schema.get("required", []))
#         fields = {}
#         for field_name, field_schema in properties.items():
#             if "anyOf" in field_schema:
#                 allowed_types = []
#                 for option in field_schema["anyOf"]:
#                     t = option.get("type")
#                     if t:
#                         allowed_types.append(json_type_mapping.get(t, Any))
#                 field_type = Union[tuple(allowed_types)] if allowed_types else Any
#             else:
#                 t = field_schema.get("type")
#                 field_type = json_type_mapping.get(t, Any) if t else Any

#             default = field_schema.get("default", None)
#             description = field_schema.get("description", None)
#             field_info = Field(default=default, description=description)

#             if field_name not in required:
#                 field_type = Optional[field_type]

#             fields[field_name] = (field_type, field_info)

#         return create_model(model_name, **fields)

#     for def_name, def_schema in defs.items():
#         nested_model = create_model_from_schema(def_schema, def_name)
#         nested_models[def_name] = nested_model

#     main_properties = json_schema.get("properties", {})
#     main_required = set(json_schema.get("required", []))
#     main_fields = {}

#     for prop_name, prop_schema in main_properties.items():
#         if "$ref" in prop_schema:
#             ref = prop_schema["$ref"]
#             ref_parts = ref.split("/")
#             if len(ref_parts) >= 3 and ref_parts[1] == "$defs":
#                 def_name = ref_parts[2]
#                 field_type = nested_models.get(def_name, dict)
#             else:
#                 field_type = dict
#         elif prop_schema.get("type") == "array":
#             items_schema = prop_schema.get("items", {})
#             if "$ref" in items_schema:
#                 ref = items_schema["$ref"]
#                 ref_parts = ref.split("/")
#                 if len(ref_parts) >= 3 and ref_parts[1] == "$defs":
#                     def_name = ref_parts[2]
#                     field_type = List[nested_models.get(def_name, dict)]
#                 else:
#                     field_type = list
#             else:
#                 t = items_schema.get("type")
#                 field_type = List[json_type_mapping.get(t, Any)] if t else list
#         else:
#             t = prop_schema.get("type")
#             field_type = json_type_mapping.get(t, str) if t else str

#         default = prop_schema.get("default", None)
#         description = prop_schema.get("description", None)
#         field_info = Field(default=default, description=description)

#         if prop_name not in main_required:
#             field_type = Optional[field_type]

#         main_fields[prop_name] = (field_type, field_info)

#     model_name = json_schema.get("title", "DynamicModel")
#     main_model = create_model(model_name, **main_fields)
#     def to_json_string(self):
#         logger.debug("Converting model to JSON string")
#         return json.dumps(self.model_dump(mode='json'), indent=4)
        
#     setattr(main_model, 'to_json_string', to_json_string)
#     return main_model


def generate_dynamic_prompt(fields: dict):
    """
    Generates a dynamic prompt and mapping dictionary based on schema fields.
    
    Parameters:
        fields (dict): A dictionary where keys are schema variable names and
                       values are descriptions (not used for the prompt here).
    
    Returns:
        tuple: (prompt: str, mapping: dict) where:
            - prompt is a string containing the dynamically generated extraction prompt.
            - mapping is a dictionary mapping lower-case, space-separated keys to schema variable names.
    """
    mapping = {}
    prompt_items = []
    for field in fields:
        # Convert field names to a more readable format.
        display_key = field.replace('_', ' ')
        mapping[display_key] = field
        prompt_items.append(f"- {display_key}")

    prompt = f"""
Please read the provided PDF thoroughly and extract the following quantities. Your output must be a table with two columns: "Quantity" and "Extracted Value". For each of the items listed below, provide the extracted value exactly as it appears in the document. If an item is not found, simply enter "N/A" for that field. Ensure that any numerical values include their associated units (if applicable) and that you handle multiple values consistently.

Extract the following items:
{chr(10).join(prompt_items)}

Instructions:
1. Analyze the entire PDF document to locate all references to the above items.
2. Extract each quantity with precision; include any units and relevant details.
3. If multiple values are present for a single item, list them clearly (e.g., separated by commas).
4. Format your output strictly as a table with two columns: one for the "Quantity" and one for the "Extracted Value".
5. Do not include any extra text, headings, or commentary—only the table is required.
6. If an item cannot be found, record it as "N/A" in the "Extracted Value" column.
"""
    return prompt, mapping

def validate_keys_are_snake_case(user_fields):
    """
    Validates that all keys in the user_fields dictionary adhere to snake_case naming conventions.

    Parameters:
        user_fields (dict): A dictionary with keys to validate.

    Returns:
        bool: True if all keys are valid; raises ValueError otherwise.
    """
    snake_case_pattern = re.compile(r'^[a-z]+(_[a-z\d]+)*$')
    for key in user_fields.keys():
        if not snake_case_pattern.match(key):
            raise ValueError(f"Invalid key '{key}': Keys must be in snake_case format.")
    return True

def display_schema_as_disabled_form(schema: dict):
    # Navigate to the nested properties
    extract_data_props = schema.get("$defs", {}).get("Extract_Data", {}).get("properties", {})
    
    if not extract_data_props:
        st.warning("No properties found in schema under $defs -> Extract_Data -> properties. for displaying")
        return

    st.header("Extract Data Form (Read-only)")

    for key, field_def in extract_data_props.items():
        field_title = field_def.get("title", key)
        default_val = field_def.get("default", "")
        description = field_def.get("description", None)  # NEW: Try to fetch description
        
        # Show the default value as a disabled text input
        st.text_input(label=key, value=str(field_title) if field_title is not None else "", disabled=True)

        # Optional: Show description if available
        if description:
            st.text_area(label="Description",value=f"{description}",disabled=True)

        # Optional: Show accepted types if anyOf is defined
        if "anyOf" in field_def:
            types = [x.get("type", "any") for x in field_def["anyOf"] if isinstance(x, dict) and "type" in x]
            type_str = ", ".join(set(types))
            st.markdown(f"*Accepted types*: `{type_str}`")

def gen_field_titles(schema:dict)-> dict:
    """
    Generates a mapping dictionary from the schema.
    
    Parameters:
        schema (dict): The schema dictionary to map.
    
    Returns:
        dict: A mapping dictionary with lower-case, space-separated keys.
    """
    # Navigate to the nested properties
    extract_data_props = schema.get("$defs", {}).get("Extract_Data", {}).get("properties", {})
    
    if not extract_data_props:
        st.warning("No properties found in schema under $defs -> Extract_Data -> properties.")
        return
    fields={}
    for key, field_def in extract_data_props.items():
        field_title = field_def.get("title", key)
        description = field_def.get("description", None)  # NEW: Try to fetch description
        
        fields.update({key:description})
        # Show the default value as a disabled text input
        
    
    return fields


if st.session_state.logged_in:

    # Initialize session state for storing the dynamic rows and the schema
    if 'row_ids' not in st.session_state:
        st.session_state['row_ids'] = [0]  # Start with one row with ID 0
        st.session_state['next_id'] = 1    # Next ID to assign

    if 'var_dict' not in st.session_state:
        st.session_state['var_dict'] = {}
    if 'prompt' not in st.session_state:
        st.session_state['prompt'] = ""
        st.session_state.mapping = None

    # Retrieve any existing Pydantic schemas from the database
    if 'pydantic_schema' not in st.session_state:
        st.session_state.pydantic_schema = get_pydantic_models(st.session_state.user_id)
        st.session_state.current_schema =None

    def add_more():
        # Add a new row with a unique ID
        st.session_state['row_ids'].append(st.session_state['next_id'])
        st.session_state['next_id'] += 1

    def delete_row(row_id):
        # Remove the row with the specified ID (prevent deletion of the first row, ID 0)
        if row_id != 0 and row_id in st.session_state['row_ids']:
            st.session_state['row_ids'].remove(row_id)

    # Display clear instructions to the user
    st.title("Extraction Data Schema Form")
    st.markdown(
        """
        **Instructions:**
        
        1. **Select or Create a Schema:**  
        Use the options below to either select an existing schema (stored in the database) or create a new one.
        
        2. **Enter Variable Names and Descriptions:**  
        If you choose to create a new schema, please enter a variable name and its corresponding description in the form below.  
        **Note:** *Variable names must follow snake_case conventions* (e.g., `variable_name`, `my_var`).
        
        3. **Add More Fields:**  
        Click the **"Add more"** button to add another variable and description pair.
        
        4. **Submit the Form:**  
        After entering all desired variable pairs, click **"Submit"**.  
        The app will validate the variable names and generate a dynamic prompt along with a mapping dictionary.
        """
    )

    # Option for user to choose an existing schema or create a new one
    schema_mode = st.radio("Select Schema Mode", ["Select existing schema", "Create new schema"])

    if schema_mode == "Select existing schema":
        if st.session_state.pydantic_schema:
            # Build options for the select box
            print("\n=================\n",st.session_state.pydantic_schema,"\n======================\n")
            schema_options = {}
            for idx, model in enumerate(st.session_state.pydantic_schema):
                # You might need to adjust the following display based on your model attributes
                label = f"Schema {idx+1}"
                schema_options[label] = model

            selected_label = st.selectbox("Select an existing schema", list(schema_options.keys()))
            selected_schema = schema_options[selected_label]
            display_schema_as_disabled_form(selected_schema.model_json_schema())
            if st.button("Submit"):
                # If the user selects an existing schema, proceed to the next page
                st.session_state.var_dict = gen_field_titles(selected_schema.model_json_schema())
                try:
                    validate_keys_are_snake_case(st.session_state.var_dict)
                except ValueError as e:
                    if "additionalProperties" in str(e):
                        pass
                    else:
                        st.error(str(e))
                # Store the selected schema in session state and update the Pydantic schema list
                dynamic_prompt, mapping = generate_dynamic_prompt(gen_field_titles(selected_schema.model_json_schema()))
                st.session_state.prompt = dynamic_prompt
                st.session_state.mapping = mapping
                st.session_state.pydantic_schema = [selected_schema]
                st.session_state.current_schema = selected_schema
                logger.info("Updated pydantic models for user %s: %s", st.session_state.user_id, st.session_state.pydantic_schema)
                st.success("Schema and prompt selected and generated successfully!")
                st.markdown("#### Mapping of variable name")
                st.write(mapping)
                st.markdown("#### Dynamically generated prompt according to schema")
                st.markdown(dynamic_prompt)
                st.markdown("#### Schema")
                st.json(selected_schema.model_json_schema())
                time.sleep(2)
                st.switch_page("structured_output.py")
            
            if st.button("Delete this Schema"):
                delete_pydantic_model(st.session_state.user_id, selected_schema)
                st.session_state.pydantic_schema = get_pydantic_models(st.session_state.user_id)
                st.rerun()
        else:
            st.info("No existing schemas found. Please create a new schema.")
            schema_mode = "Create new schema"  # Force new schema creation

    if schema_mode == "Create new schema":
        # Create a form to batch the inputs for creating a new schema
        with st.form(key="variable_form"):
            st.subheader("Enter your variables and descriptions")
            
            # Display input fields for each row
            for row_id in st.session_state['row_ids']:
                col1, col2 = st.columns([1, 2])
                with col1:
                    st.text_input(
                        label="Variable name",
                        key=f"var_{row_id}",
                        placeholder="Enter snake_case variable name"
                    )
                with col2:
                    st.text_area(
                        label="Description",
                        key=f"desc_{row_id}",
                        placeholder="Enter description",
                        height=100
                    )
            
            # Add buttons for form submission, adding more fields, and deletion
            col1, col2, col3 = st.columns(3)
            with col1:
                submit_button = st.form_submit_button("Submit")
            with col2:
                add_button = st.form_submit_button("Add more", on_click=add_more)
            with col3:
                if len(st.session_state['row_ids']) > 1:
                    delete_button = st.form_submit_button("Delete", on_click=delete_row,
                                                            args=(st.session_state['row_ids'][-1],))
                else:
                    st.write("Cannot delete the only row.")

        # Process form submission
        if submit_button:
            # Build dictionary from input fields
            result_dict = {}
            for row_id in st.session_state['row_ids']:
                var_key = st.session_state.get(f"var_{row_id}")
                var_value = st.session_state.get(f"desc_{row_id}")
                if var_key and var_key.strip():  # Only add non-empty keys
                    result_dict[var_key.strip()] = var_value.strip() if var_value else ""
            
            try:
                # Validate that all keys are in snake_case
                validate_keys_are_snake_case(result_dict)
            except ValueError as e:
                st.error(str(e))
            # Store the validated dictionary in session state and update the Pydantic schema list
            st.session_state['var_dict'] = result_dict
            new_model = DynamicGenSchema.create_model(result_dict)
            st.session_state.pydantic_schema.append(new_model)
            st.session_state.current_schema = new_model
            update_pydantic_models(st.session_state.user_id, st.session_state.pydantic_schema)
            
            logger.info("Updated pydantic models for user %s: %s", st.session_state.user_id, st.session_state.pydantic_schema)
            st.write("**Final Dictionary:**")
            st.json(result_dict)
            
            # Generate and display the dynamic prompt
            dynamic_prompt, mapping = generate_dynamic_prompt(result_dict)
            st.session_state.prompt = dynamic_prompt
            st.session_state.mapping = mapping
            
            # Optionally, navigate to another page
            time.sleep(2)
            # st.switch_page("structured_output.py")
else:
    st.warning("Please log in to access this page.")
    st.switch_page("login.py")