import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
import re

def save_mappings(html_elements: dict, profile_id: str) -> None:
    """
    Saves the mapped data to JSON files with timestamp and profile ID
    
    Args:
        logical_groups: Dictionary of logically grouped data
        html_elements: Dictionary of HTML element mappings
        profile_id: Profile identifier from the source data
    """
    # Create output directory if it doesn't exist
    output_dir = Path("profile_mappings")
    output_dir.mkdir(exist_ok=True)
    
    # Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save HTML elements
    html_file = output_dir / f"html_elements_{profile_id}_{timestamp}.json"
    with open(html_file, 'w', encoding='utf-8') as f:
        json.dump(html_elements, f, indent=2)
    
    print(f"Saved HTML elements to: {html_file}")


class WasteProfileMapper:
    def __init__(self):
        # Same value mappings as before

        self.flash_point_mapping = {
            "< 73°F": "< 73 F",
            "≥ 73°F to < 100°F": "73 - 99 F",
            "≥ 100°F to < 140°F": "100 - 139 F",
            "≥ 140°F to < 200°F": "140 - 200 F",
            "≥ 200°F": "> 200 F",
            "N/A": "NONE"
        }
        
        self.odor_mapping = {
            "None": "NONE",
            "Mild": "MILD",
            "Strong": "STRONG"
        }

    def map_profile(self, data: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Maps WASTELINQ profile data to both logical groups and HTML element IDs
        
        Args:
            data: Dictionary containing WASTELINQ profile data
            
        Returns:
            html_element_mapping
        """

        
        # Map to HTML elements
        html_elements = self._create_html_mapping(data)
        
        return html_elements

    def _create_html_mapping(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Creates mapping for HTML form elements"""

        special_contents = self._determine_special_contents(data) 

        html_mapping = {
            # Waste Stream section
            "__input3-__clone50-inner": data.get("CustomerProfile_id"), # WASTELINQ PROFILE NUMBER
            "__input3-__clone52-inner": data.get("StateWasteCode"), # Texas state code
            "__input3-__clone54-inner": data.get("Profile_Name", ""),  # Common Name 
            "__area1-__clone56-inner": data.get("ProcessGeneratingTheWaste", ""),  # Process Description
            "__box1-__clone58-inner": "Y" if data.get("RCRAExempt") == "Yes" else "N",  # RCRA Exempt
            "__box1-__clone62-inner": "Y" if data.get("CERCLAregulatortedWaste") == "Yes" else "N",  # CERCLA
            "__box2-__clone64-inner": self._get_waste_determination(data),  # Waste Determination
            "__box1-__clone68-inner": self._extract_epa_form_code(data.get("EPAFormCode", "")),  # Form Code - standardized
            "__box1-__clone70-inner": data.get("EPASourceCode", "") if data.get("EPASourceCode", "") != 'N/A' else "NULL - NO VALUE",  # Source Code


            # Waste Characteristics section
            "__box3-__clone72-inner": self._map_special_characteristics(data),  # Special Characteristics 
            "__input4-__clone74-inner": data.get("PCPViscosity", "").split(" - ")[0] if data.get("PCPViscosity") else "",  # Viscosity
            "__input4-__clone76-inner": data.get("PCSpecificGravity", ""), # Specific Gravity
            "__input4-__clone78-inner": data.get("PCPTotalOrganicCarbonValue", ""), # Total Organic Carbon (TOC)
            # "__input4-__clone80-inner": data.get("Halogen %"), ### Total Halogens % (NOT IMPLEMENTED, REASON: we just have yes or no, they need a percent)
            # "__input4-__clone82-inner": data.get("VOC %"),  ### VOC % (NOT IMPLEMENTED, REASON: we just have yes or no, they need a percent)
            "__box4-__clone84-inner": self.odor_mapping.get(data.get("PCPOdor", ""), ""),  # Odor
            "__input4-__clone86-inner": data.get("PCPOdor_Radio_Plus_Option", ""),  # Odor Description
            "__input4-__clone88-inner": data.get("PCPColor", ""),  # Color
            "__box4-__clone90-inner": self._determine_physical_state(data),  # Physical State
            "__box4-__clone94-inner": self._map_phases(data),  # Phases
            "__box4-__clone98-inner": self._determine_btu_range(data.get("PCPBTUValue", "")), # BTU Mapping            
            "__box4-__clone100-inner": self._map_ph(data),  # pH
            "__box4-__clone102-inner": self._map_flash_point(data),  # Flash Point
            # "__input4-__clone104-inner": data.get("PCPBoilingPointValue")  ### Boiling point (NOT IMPLEMENTED, REASON: We have a range, they ask for exact value)
            
            # Additional Information
            "__box9-__clone107-inner": special_contents,  # Special Contents and Characteristics
            "__input8-__clone109-inner": data.get("PCPOtherPropertiesMetalFines_Description", "") if "METAL PIECES" in special_contents or "METAL POWDER OR FLAKE" in special_contents else "",
            "__input8-__clone111-inner": data.get("PCPOtherPropertiesReactiveCyanides_Range", "0"),  # Cyanide Level
            "__input8-__clone113-inner": data.get("PCPOtherPropertiesReactiveSulfides_Range", "0"),  # Sulfides Level
            # "__box10-__clone115-inner": data.get("TSCAregulatortedPCBWaste_Range", "") if "PCBS" in special_contents else "",  # PCB Range (NOT IMPLEMENTED, REASON: Certification form required)
            "__box10-__clone117-inner": "Y" if data.get("BenzeneNESHAPWaste") == "Yes" else "N",  # Benzene NESHAP
            "__box10-__clone119-inner": "Y" if data.get("UsedOil") == "Yes" else "N",  # Used Oil
            # "__box10-__clone121-inner": self._check_halogen_limit(data),  # Halogens exceed 1,000ppm (NOT IMPLEMENTED, REASON: Need % to estimate, we have yes/no)
            "__box10-__clone123-inner": "Y" if data.get("HalogenatedOrganicCompound") == "Yes" or self._check_common_chlorinated_constituents(data) else "N",  # Chlorinated Constituent
            "__box10-__clone125-inner": "N",  # Rebut hazardous presumption (default No)
            "__box10-__clone127-inner": "Y" if data.get("Regulatory500PPMVOC") == "Yes" else "N",  # VOC > 500ppm
            "__box10-__clone131-inner": "Y" if self._check_pfas(data) else "N",  # PFAS content

            # RCRA Characterization section
            "__box11-__clone133-inner": "Y" if data.get("HazardousWaste") == "Yes" else "N",  # RCRA Hazardous
            "__box11-__clone135-inner": "Y" if data.get("UniversalWaste") == "Yes" else "N",  # Universal Waste
            "__box11-__clone137-inner": "Y" if self._search_all_fields_for_terms(data, ['F006', 'F019']) else "N", # does waste treatment generate F006, or F019 Sludge
            "__box12-__clone139-inner": self._get_waste_codes(data),  # Waste Codes
            "__box11-__clone145-inner": "Y" if data.get('RegulatoryLDRSubcategory') == "Wastewater"  else "N",
            "__box11-__clone147-inner": "N" if data.get('RegulatoryLDRSubcategory') != "Wastewater"  else "Y",

            # Validated up to here
            # Shipping Information section
            "__box13-__clone149-inner": "Y" if data.get("TransportationRequirement") == "Bulk Liquid" else "N",  # Bulk Liquid
            "__input9-__clone151-inner": str(data.get("ShippingAndPackagingVolume")) + ' ' + data.get("ShippingAndPackagingVolumeType", ""), # Solid Volume and unit of measurement
            "__box13-__clone153-inner": "Y" if data.get("TransportationRequirement") == "Bulk Solid" else "N",  # Bulk Solid
            "__input9-__clone155-inner": str(data.get("ShippingAndPackagingVolume")) + ' ' + data.get("ShippingAndPackagingVolumeType", ""), # Liquid Volume and unit of measurement
            "__box13-__clone157-inner": "Y" if data.get("TransContainer_PortableToteTank") == "TRUE" else "N", 
            "__box14-__clone159-inner": ["METAL", "PLASTIC IN METAL CAGE"], # Tote container type (default to both)
            "__box14-__clone161-inner": self._map_container_sizes(data), # Container Sizes
            # "__box14-__clone163-inner": 0, # Container type (NOT IMPLEMENTED, REASON: We don't have a way to specify container type [FIBERBOARD, METAL, PLASTIC])
            "__box13-__clone167-inner": self._map_frequency(data.get("ShippingAndPackagingFrequency", "")),  # Frequency
            "__input9-__clone171-inner": 5,  # Quantity (default to 5, doesn't matter for Tradebe)
            "__box13-__clone173-inner": "Y" if data.get("ShippingAndPackagingWasteCombinationPackage") == "Yes" else "N",
            
            # DOT Information section
            "__box15-__clone175-inner": "Y" if data.get("ShippingAndPackagingUSDOT") == "Yes" else "N",  # DOT Hazmat
            "__vol0-inner": self._extract_un_na_code(data),  # DOT Shipping Name
            "__box15-__clone178-inner": self._is_rcra_waste(data), # Is RCRA waste?
            "__area2-__clone180-inner": self._extract_constituents(data), # Techical Descriptors, Get chemical consituents in parenthesis of USDOTComment
            "__input10-__clone182-inner": self._extract_rq_info(data),  # "Reportable Quantity (RQ)"
            "__box15-__clone184-inner": self._has_dot_special_permit(data),  # "DOT Special Permit for Transportation"
            "__input10-__clone186-inner": self._extract_special_permit_number(data), # Extract Special Permit if necessary
    
        }

        # Add chemical composition if available
        # NOTE: Chemical names are added last, otherwise they  
        # get reset if they are not in Tradebe's list

        if data.get("ChemicalPhysicalComposion"):
            chemicals = data.get("ChemicalPhysicalComposion").split(",")
            cas_numbers = data.get("CAS", "").split(",")
            max_values = data.get("Max", "").split(",")
            min_values = data.get("Min", "").split(",")
            
            for i, (chem, cas, minimum, maximum) in enumerate(zip(chemicals, cas_numbers, min_values, max_values)):

                base_index = 191
                if i > 0:
                    base_index = 191 + 3 + 10*i # difference between the first row and second is 13, difference between all following rows is 10

                # html_mapping[f"__input5-__clone{base_index}-inner"] = chem.strip()
                html_mapping[f"__cas0-__clone{base_index + 1}-inner"] = cas.strip()
                html_mapping[f"__input6-__clone{base_index + 2}-inner"] = minimum.strip() 
                html_mapping[f"__input7-__clone{base_index + 3}-inner"] = maximum.strip()

            # Doing chemical names last
            for i, (chem, cas, minimum, maximum) in enumerate(zip(chemicals, cas_numbers, min_values, max_values)):

                base_index = 191
                if i > 0:
                    base_index = 191 + 3 + 10*i 

                html_mapping[f"__input5-__clone{base_index}-inner"] = chem.strip()

        return html_mapping

    def _search_all_fields_for_terms(self, data: Dict[str, Any], terms: List[str]) -> bool:

        relevant_keys = [
            'Profile_Name', 'ProcessGeneratingTheWaste', 'ChemicalPhysicalComposion (coma separated)'
            'ShippingAndPackagingUSDOTComment', 'fddTechName', 'fddRQ', 'fddDOTNotesSpecialPermits'
            ]
        
        for value in data.values():
            # Convert value to string and lowercase for comparison
            if value is not None:
                str_value = str(value).lower()
                if any(term in str_value for term in terms):
                    return True
        return False

    def _get_waste_determination(self, data: Dict[str, Any]) -> List[str]:
        """Determines waste determination methods"""
        methods = []
        if data.get("WasteDetermination_GenKnowledge") == True:
            methods.append("Generator Knowledge")
        if data.get("WasteDetermination_SDS") == True:
            methods.append("SDS/MSDS")
        if data.get("WasteDetermination_WasteAnylysis") == True:
            methods.append("Testing")
        return methods

    def _extract_epa_form_code(self, form_code: str) -> str:

        if not form_code:
            return ""
            
        pattern = r'W\d{3}'
        matches = re.findall(pattern, form_code)
        return matches[0] if matches else "NONE"

    def _map_special_characteristics(self, data: Dict[str, Any]) -> List[str]:

        characteristics = []
        
        # Direct mappings from PCPOtherProperties fields
        property_mappings = {
            "PCPOtherPropertiesOxidizer": "OXIDIZER",
            "PCPOtherPropertiesExplosive": "EXPLOSIVE",
            "PCPOtherPropertiesShockSensitive": "SHOCK SENSITIVE",
            "PCPOtherPropertiesWaterReactive": "WATER REACTIVE",
            "PCPOtherPropertiesRadioactive": "RADIOACTIVE",
            "PCPOtherPropertiesPolymerizable": "POLYMERIZER",
            "PCPOtherPropertiesAirReactive": "AIR REACTIVE",
            "PCPOtherPropertiesPyrophoric": "PYROPHORIC",
            "PCPOtherPropertiesOrganaicPeroxides": "ORGANIC PEROXIDE",
            "PCPOtherPropertiesDioxins": "DIOXIN OR SUSPECT",
        }
        
        # Add characteristics from direct property mappings
        for wastelinq_field, tradebe_char in property_mappings.items():
            if data.get(wastelinq_field) == True:
                characteristics.append(tradebe_char)
        
        # Check chemical composition for specific indicators
        composition = str(data.get("ChemicalPhysicalComposion", "")).lower()
        
        # Check for hexavalent chromium/hexachrome
        if any(term in composition for term in ["hexavalent chromium", "cr(vi)", "cr6+", "hexachrome"]):
            characteristics.append("HEXACROME")
        
        # Check for chelating agents
        if any(term in composition for term in ["edta", "chelat", "sequester"]):
            characteristics.append("CHELATING AGENT")
        
        # Check for lachrymators
        if any(term in composition for term in ["tear gas", "lachrymator", "cs gas", "pepper spray"]):
            characteristics.append("LACHRYMATOR")
        
        # Check for inhalation hazards
        if any(term in composition for term in ["toxic by inhalation", "inhalation hazard", "poison by inhalation"]):
            characteristics.append("INHALATION HAZARD")
        
        # Check for fuming characteristics
        if any(term in composition for term in ["fuming", "fumes", "oleum"]):
            characteristics.append("FUMING")
        
        # Check for infectious waste/biohazard
        if data.get("MedicalWaste") == "Yes":
            characteristics.append("INFECTIOUS WASTE")
        
        # Check for temperature control requirements
        if any(term in str(data.get("TransportationRequirement", "")).lower() 
            for term in ["temperature controlled", "temp control", "refrigerated"]):
            characteristics.append("TEMPERATURE CONTROLLED")
        
        # Check for DEA regulated substances
        if any(term in composition for term in ["controlled substance", "dea regulated", "schedule i", "schedule ii"]):
            characteristics.append("DEA REGULATED SUBSTANCE")
        
        # Remove duplicates while maintaining order
        return list(dict.fromkeys(characteristics))

    def _determine_physical_state(self, data: Dict[str, Any]) -> str:

        def is_true(value: Any) -> bool:
            """Helper function to check if a value represents True"""
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                return value.upper() in ('TRUE', 'YES', '1')
            return False

        states = {
            "SOLID": is_true(data.get("PCPhysicalStateSolid2")),
            "LIQUID": is_true(data.get("PCPPhysicalStateLiquid2")),
            "SLUDGE": is_true(data.get("PCPPhysicalStateSludge2")),
            "GAS": is_true(data.get("PCPPhysicalStateGas2"))
        }
        
        true_states = [state for state, value in states.items() if value]

        # If no states are True, return empty string
        if not true_states:
            return ""
            
        # If multiple states are True, prioritize in this order
        priority_order = ["LIQUID", "SLUDGE", "SOLID", "GAS"]
        for state in priority_order:
            if state in true_states:
                return state
                
        # If none of the priority states match, return the first true state
        return true_states[0]

    def _map_phases(self, data: Dict[str, Any]) -> str:

        phase_count = data.get("PCNumberOfPhases_Layer", "1")
        
        if not phase_count or phase_count == "":
            return "SINGLE"  # Default to single phase if no data
            
        try:
            phase_count = str(phase_count).strip().upper()
            
            # Map based on value
            if phase_count in ["1", "SINGLE"]:
                return "SINGLE"
            elif phase_count in ["2", "DOUBLE", "TWO"]:
                return "DOUBLE"
            elif phase_count in ["3", "THREE", "MORE THAN 3", "MULTIPLE", "MULTI"]:
                return "MULTI"
            else:
                # Try to convert to number if it's numeric
                num_phases = float(phase_count)
                if num_phases == 1:
                    return "SINGLE"
                elif num_phases == 2:
                    return "DOUBLE"
                else:
                    return "MULTI"
        except (ValueError, TypeError):
            return "SINGLE"  # Default to single phase if conversion fails

    def _determine_btu_range(self, wastelinq_btu: str) -> str:
        
        # Mapping logic
        if wastelinq_btu == "0 - 4999":
            # For 0-4999 range, select the appropriate sub-range
            # Default to middle range if no additional info
            return "3,000 - 5,000"
            
        elif wastelinq_btu == "5,000 - 10,000":
            return "5,000 - 10,000"
            
        elif wastelinq_btu == "> 10,000":
            return "> 10,000 (EX. OIL)"
        
        else:
            return ""
    
    def _map_ph(self, data: Dict[str, Any]) -> str:

        ph_value = data.get("PCpH")
        custom_value = data.get("pc_ph_radio_plus_option")
        
        # Handle N/A case first
        if not ph_value or ph_value == "N/A":
            return "NA"
            
        # Handle standard ranges
        standard_mapping = {
            "≤ 2": "< =2.0",
            "> 2 to ≤ 5": "2.1-4.0",
            "> 5 to ≤ 10": "4.1-10.0",
            "> 10 to ≤ 12.5": "10.1-12.4",
            "≥ 12.5": ">=12.4"
        }
        
        if ph_value in standard_mapping:
            return standard_mapping[ph_value]
            
        # Handle custom value
        if ph_value == "Custom" and custom_value:
            try:
                ph_num = float(custom_value)
                
                # Map the custom value to the appropriate range
                if ph_num <= 2.0:
                    return "< =2.0"
                elif 2.0 < ph_num <= 4.0:
                    return "2.1-4.0"
                elif 4.0 < ph_num <= 10.0:
                    return "4.1-10.0"
                elif 10.0 < ph_num <= 12.4:
                    return "10.1-12.4"
                else:
                    return ">=12.4"
            except (ValueError, TypeError):
                return "NA"  # If custom value isn't a valid number
                
        return "NA"  # Default case

    def _map_flash_point(self, data: Dict[str, Any]) -> str:
        """
        Maps WASTELINQ flash point ranges to Tradebe's flash point options
        
        Args:
            data: Dictionary containing PCFlashPoint and any actual flash point value
            
        Returns:
            String matching Tradebe's flash point range options
        """
        flash_point = data.get("PCFlashPoint")
        actual_value = data.get("PCFlashPoint_Actual")
        
        # Handle N/A case first
        if not flash_point or flash_point == "N/A":
            return "NONE"
            
        # Standard range mapping
        standard_mapping = {
            "< 73°F": "< 73 F",
            "≥ 73°F to < 100°F": "73 - 99 F",
            "≥ 100°F to < 140°F": "100 - 139 F",
            "≥ 140°F to < 150°F": "140 - 200 F",  # Note: Mapped to broader Tradebe range
            "≥ 150°F to < 200°F": "140 - 200 F",  # Same broader range
            "≥ 200°F": "> 200 F"
        }
        
        if flash_point in standard_mapping:
            return standard_mapping[flash_point]
            
        # Handle actual/custom value
        if flash_point == "Actual" and actual_value:
            try:
                fp_num = float(actual_value)
                
                # Map the actual value to the appropriate range
                if fp_num < 73:
                    return "< 73 F"
                elif 73 <= fp_num < 100:
                    return "73 - 99 F"
                elif 100 <= fp_num < 140:
                    return "100 - 139 F"
                elif 140 <= fp_num <= 200:
                    return "140 - 200 F"
                else:
                    return "> 200 F"
            except (ValueError, TypeError):
                return "NONE"  # If actual value isn't a valid number
                
        return "NONE"  # Default case

    def _determine_special_contents(self, data: Dict[str, Any]) -> List[str]:
        """Determines special contents for waste stream"""
        special_contents = []
        
        # Check metal pieces and powder
        if data.get("PCPOtherPropertiesMetalFines") == True:
            special_contents.append("METAL PIECES")
            metal_terms = ["metal powder", "metal flake", "metal dust"]
            if self._search_all_fields_for_terms(data, metal_terms):
                special_contents.append("METAL POWDER OR FLAKE")

        # Check asbestos
        if data.get("PCPOtherPropertiesAbestosFriable") == True or data.get("PCPOtherPropertiesAbestosNonFriable") == True:
            special_contents.append("ASBESTOS")
        
        # Check reactive materials
        if data.get("PCPOtherPropertiesReactiveCyanides") == True:
            special_contents.append("REACTIVE CYANIDE")
        if data.get("PCPOtherPropertiesReactiveSulfides") == True:
            special_contents.append("REACTIVE SULFIDE")
        
        # Check PCBs
        if data.get("TSCAregulatortedPCBWaste") == "Yes":
            special_contents.append("PCBS")
        
        # Check all fields for specific substances
        if self._search_all_fields_for_terms(data, ["HYDROFLUORIC ACID"]):
            special_contents.append("HYDROFLUORIC ACID")
        if self._search_all_fields_for_terms(data, ["NITRIC ACID"]):
            special_contents.append("NITRIC ACID")
        if self._search_all_fields_for_terms(data, ["ISOCYANATES", "ISOCYANATE"]):
            special_contents.append("ISOCYANATES")
        if self._search_all_fields_for_terms(data, ["NITROCELLULOSE"]):
            special_contents.append("NITROCELLULOSE")
        if not self._search_all_fields_for_terms(data, ['no sharps']) and not self._search_all_fields_for_terms(data, ['sharps']):
            special_contents.append("SHARPS")

        return special_contents
    
    def _check_halogen_limit(self, data: Dict[str, Any]) -> str:
        """Checks if halogen content exceeds 1000 ppm"""
        if data.get("UsedOil") != "Yes":
            return "N"
            
        try:
            halogen_pct = float(data.get("Total Halogens %", "0") or "0")
            halogen_ppm = halogen_pct * 10000
            return "Y" if halogen_ppm > 1000 else "N"
        except ValueError:
            return "N"

    def _check_common_chlorinated_constituents(self, data: Dict[str, Any]) -> bool:

        commons = [
            'Aroclor 1242', 'Aroclor 1254', 'Aroclor 1260', 'Aroclor',
            'Trichloroethylene', 'Tetrachloroethylene', 'Carbon tetrachloride',
            'Methylene chloride', '1,1,1-Trichloroethane', 'Chlorobenzene', 
            'Dichlorobenzenes', 'Trichlorobenzenes', 'Vinyl chloride', 
            'Chloroform', '1,2-Dichloroethane', 'Pentachlorophenol', 
              'DDT', 'Chlordane', 'Dieldrin', 'Heptachlor', 'PCP'
              ]
        
        return self._search_all_fields_for_terms(data, commons)

    def _check_pfas(self, data: Dict[str, Any]) -> bool:

        pfas = [
             'Perfluorooctanoic acid', 'PFOA', 'Perfluorooctane sulfonic acid', 'PFOS', 
             'Perfluorobutane sulfonic acid', 'PFBS', 'Hexafluoropropylene oxide dimer acid', 
             'HFPO-DA', 'GenX', 'Perfluorononanoic acid', 'PFNA', 'Perfluorohexane sulfonic acid', 
             'PFHxS', 'Perfluorodecanoic acid', 'PFDA', 'Perfluorohexanoic acid', 'PFHxA', 
             'Perfluorobutanoic acid', 'PFBA', 'Polyfluorinated alkyl', 'PFAS'
        ]

        return self._search_all_fields_for_terms(data, pfas)

    def _get_waste_codes(self, data: Dict[str, Any]) -> List[str]:

        potential_codes = [
            'F001', 'F002', 'F003', 'F004', 'F005', 'F006', 'F007', 'F008', 'F009', 'F010', 'F011', 'F012', 
            'F019', 'F020', 'F021', 'F022', 'F023', 'F024', 'F025', 'F026', 'F027', 'F028', 'F032', 'F034', 
            'F035', 'F037', 'F038', 'F039', 'K001', 'K002', 'K003', 'K004', 'K005', 'K006', 'K007', 'K008', 
            'K009', 'K010', 'K011', 'K013', 'K014', 'K015', 'K016', 'K017', 'K018', 'K019', 'K020', 'K021', 
            'K022', 'K023', 'K024', 'K025', 'K026', 'K027', 'K028', 'K029', 'K030', 'K031', 'K032', 'K033', 
            'K034', 'K035', 'K036', 'K037', 'K038', 'K039', 'K040', 'K041', 'K042', 'K043', 'K044', 'K045', 
            'K046', 'K047', 'K048', 'K049', 'K050', 'K051', 'K052', 'K060', 'K061', 'K062', 'K069', 'K071', 
            'K073', 'K083', 'K084', 'K085', 'K086', 'K087', 'K088', 'K093', 'K094', 'K095', 'K096', 'K097', 
            'K098', 'K099', 'K100', 'K101', 'K102', 'K103', 'K104', 'K105', 'K106', 'K107', 'K108', 'K109', 
            'K110', 'K111', 'K112', 'K113', 'K114', 'K115', 'K116', 'K117', 'K118', 'K123', 'K124', 'K125', 
            'K126', 'K131', 'K132', 'K136', 'K141', 'K142', 'K143', 'K144', 'K145', 'K147', 'K148', 'K149', 
            'K150', 'K151', 'K156', 'K157', 'K158', 'K159', 'K161', 'K169', 'K170', 'K171', 'K172', 'K174', 
            'K175', 'K176', 'K177', 'K178', 'K181', 'P001', 'P002', 'P003', 'P004', 'P005', 'P006', 'P007', 
            'P008', 'P009', 'P010', 'P011', 'P012', 'P013', 'P014', 'P015', 'P016', 'P017', 'P018', 'P020', 
            'P021', 'P022', 'P023', 'P024', 'P026', 'P027', 'P028', 'P029', 'P030', 'P031', 'P033', 'P034', 
            'P036', 'P037', 'P038', 'P039', 'P040', 'P041', 'P042', 'P043', 'P044', 'P045', 'P046', 'P047', 
            'P048', 'P049', 'P050', 'P051', 'P054', 'P056', 'P057', 'P058', 'P059', 'P060', 'P062', 'P063', 
            'P064', 'P065', 'P066', 'P067', 'P068', 'P069', 'P070', 'P071', 'P072', 'P073', 'P074', 'P075', 
            'P076', 'P077', 'P078', 'P081', 'P082', 'P084', 'P085', 'P087', 'P088', 'P089', 'P092', 'P093', 
            'P094', 'P095', 'P096', 'P097', 'P098', 'P099', 'P101', 'P102', 'P103', 'P104', 'P105', 'P106', 
            'P108', 'P109', 'P110', 'P111', 'P112', 'P113', 'P114', 'P115', 'P116', 'P118', 'P119', 'P120', 
            'P121', 'P122', 'P123', 'P127', 'P128', 'P185', 'P188', 'P189', 'P190', 'P191', 'P192', 'P194', 
            'P196', 'P197', 'P198', 'P199', 'P201', 'P202', 'P203', 'P204', 'P205', 'U001', 'U002', 'U003', 
            'U004', 'U005', 'U006', 'U007', 'U008', 'U009', 'U010', 'U011', 'U012', 'U014', 'U015', 'U016', 
            'U017', 'U018', 'U019', 'U020', 'U021', 'U022', 'U023', 'U024', 'U025', 'U026', 'U027', 'U028', 
            'U029', 'U030', 'U031', 'U032', 'U033', 'U034', 'U035', 'U036', 'U037', 'U038', 'U039', 'U041', 
            'U042', 'U043', 'U044', 'U045', 'U046', 'U047', 'U048', 'U049', 'U050', 'U051', 'U052', 'U053', 
            'U055', 'U056', 'U057', 'U058', 'U059', 'U060', 'U061', 'U062', 'U063', 'U064', 'U066', 'U067', 
            'U068', 'U069', 'U070', 'U071', 'U072', 'U073', 'U074', 'U075', 'U076', 'U077', 'U078', 'U079', 
            'U080', 'U081', 'U082', 'U083', 'U084', 'U085', 'U086', 'U087', 'U088', 'U089', 'U090', 'U091', 
            'U092', 'U093', 'U094', 'U095', 'U096', 'U097', 'U098', 'U099', 'U101', 'U102', 'U103', 'U105', 
            'U106', 'U107', 'U108', 'U109', 'U110', 'U111', 'U112', 'U113', 'U114', 'U115', 'U116', 'U117', 
            'U118', 'U119', 'U120', 'U121', 'U122', 'U123', 'U124', 'U125', 'U126', 'U127', 'U128', 'U129', 
            'U130', 'U131', 'U132', 'U133', 'U134', 'U135', 'U136', 'U137', 'U138', 'U140', 'U141', 'U142', 
            'U143', 'U144', 'U145', 'U146', 'U147', 'U148', 'U149', 'U150', 'U151', 'U152', 'U153', 'U154', 
            'U155', 'U156', 'U157', 'U158', 'U159', 'U160', 'U161', 'U162', 'U163', 'U164', 'U165', 'U166', 
            'U167', 'U168', 'U169', 'U170', 'U171', 'U172', 'U173', 'U174', 'U176', 'U177', 'U178', 'U179', 
            'U180', 'U181', 'U182', 'U183', 'U184', 'U185', 'U186', 'U187', 'U188', 'U189', 'U190', 'U191', 
            'U192', 'U193', 'U194', 'U196', 'U197', 'U200', 'U201', 'U202', 'U203', 'U204', 'U205', 'U206', 
            'U207', 'U208', 'U209', 'U210', 'U211', 'U213', 'U214', 'U215', 'U216', 'U217', 'U218', 'U219', 
            'U220', 'U221', 'U222', 'U223', 'U225', 'U226', 'U227', 'U228', 'U234', 'U235', 'U236', 'U237', 
            'U238', 'U239', 'U240', 'U243', 'U244', 'U246', 'U247', 'U248', 'U249', 'U271', 'U278', 'U279', 
            'U280', 'U328', 'U353', 'U359', 'U364', 'U367', 'U372', 'U373', 'U387', 'U389', 'U394', 'U395', 
            'U404', 'U409', 'U410', 'U411', 'D001', 'D002', 'D003', 'D004', 'D005', 'D006', 'D007', 'D008', 
            'D009', 'D010', 'D011', 'D012', 'D013', 'D014', 'D015', 'D016', 'D017', 'D018', 'D019', 'D020', 
            'D021', 'D022', 'D023', 'D024', 'D025', 'D026', 'D027', 'D028', 'D029', 'D030', 'D031', 'D032', 
            'D033', 'D034', 'D035', 'D036', 'D037', 'D038', 'D039', 'D040', 'D041', 'D042', 'D043']
        
        waste_codes = set()

        for code in potential_codes:
            if self._search_all_fields_for_terms(data, [code]):
                waste_codes.update(code)

        # Check characteristic waste (D codes)
        d_code_mappings = {
            "WCHazardousIgnitable": "D001",
            "WCHazardousCorrosive": "D002",
            "WCHazardousReactive": "D003",
            "WCHazardousToxic": "D004"  # Add more D codes as needed
        }
    
        for field, code in d_code_mappings.items():
            if data.get(field) == "Yes":
                waste_codes.add(code)
                
        # Get F-listed codes
        if data.get("WCHazardousF") == "Yes":
            f_codes = data.get("hazardouswastenof", "")
            if f_codes:
                # Clean and split the codes
                f_codes = [code.strip().upper() for code in f_codes.split(",") if code.strip()]
                # Validate format (F followed by 3 digits)
                f_codes = [code for code in f_codes if code.startswith('F') and 
                        len(code) == 4 and code[1:].isdigit()]
                waste_codes.update(f_codes)
        
        # Get K-listed codes
        if data.get("WCHazardousK") == "Yes":
            k_codes = data.get("hazardouswastenoK", "")
            if k_codes:
                k_codes = [code.strip().upper() for code in k_codes.split(",") if code.strip()]
                k_codes = [code for code in k_codes if code.startswith('K') and 
                        len(code) == 4 and code[1:].isdigit()]
                waste_codes.update(k_codes)
        
        # Get P-listed codes
        if data.get("WCHazardousP") == "Yes":
            p_codes = data.get("hazardouswastenoP", "")
            if p_codes:
                p_codes = [code.strip().upper() for code in p_codes.split(",") if code.strip()]
                p_codes = [code for code in p_codes if code.startswith('P') and 
                        len(code) == 4 and code[1:].isdigit()]
                waste_codes.update(p_codes)
        
        # Get U-listed codes
        if data.get("WCHazardousU") == "Yes":
            u_codes = data.get("hazardouswastenoU", "")
            if u_codes:
                u_codes = [code.strip().upper() for code in u_codes.split(",") if code.strip()]
                u_codes = [code for code in u_codes if code.startswith('U') and 
                        len(code) == 4 and code[1:].isdigit()]
                waste_codes.update(u_codes)
                
        # State waste codes (if needed)
        state_code = data.get("StateWasteCode", "")
        if state_code:
            waste_codes.add(state_code)
        
        # Convert set to sorted list for consistent output
        return sorted(list(waste_codes))

    def _map_container_sizes(self, data: Dict[str, Any]) -> List[str]:

        container_sizes = []
        
        # Check Portable Tote Tank
        if data.get("TransContainer_PortableToteTank") == True:
            tote_size = data.get("TransContainer_PortToteTankSize", "")
            if tote_size:
                try:
                    size = float(tote_size)
                    if size < 275:
                        container_sizes.append("<275 GALLON TOTE")
                    elif 275 <= size <= 330:
                        container_sizes.append("275-330 GALLON TOTE")
                    elif 330 < size <= 500:
                        container_sizes.append("331-500 GALLON TOTE")
                except ValueError:
                    pass

        # Check Drum
        if data.get("TransContainer_Drum") == True:
            drum_size = data.get("TransContainer_DrumSize", "")
            if drum_size:
                size_mapping = {
                    "5 G": "5 GALLON CONTAINER",
                    "15 G": "15 GALLON CONTAINER",
                    "30 G": "30 GALLON CONTAINER",
                    "55 G": "55 GALLON CONTAINER"
                }
                for key, value in size_mapping.items():
                    if key in drum_size:
                        container_sizes.append(value)

        # Check Cubic Yard Box
        if data.get("TransContainer_CubicYardBox") == True:
            container_sizes.append("CUBIC YARD BOX")

        # Check Box/Carton/Case
        if data.get("TransContainer_BoxCartonCase") == True:
            # Could be PGI BOX, bulb boxes, or lab pack - would need additional field to determine
            container_sizes.append("PGI BOX")  # Default if no specific type indicated

        # Check Bulk Liquid Transport
        if data.get("TransBulkType_TankTruck") == True:
            container_sizes.append("TANKER")

        # Check Roll-Off
        if data.get("TransBulkType_RollOff") == True:
            container_sizes.append("ROLL OFF")

        # If no specific container types are found
        if not container_sizes:
            container_sizes.append("NONE")

        return container_sizes

    def _map_frequency(self, freq: str) -> str:
        """Maps shipping frequency to Tradebe format"""
        mapping = {
            "One Time": "ONE TIME SHIPMENT",
            "Monthly": "PER MONTH",
            "Quarterly": "PER QUARTER",
            "Annually": "PER YEAR",
            "Other": "ONE TIME SHIPMENT"
        }
        return mapping.get(freq, "AS NEEDED")

    def _extract_un_na_code(self, data: Dict[str, Any]) -> str:

        shipping_desc = data.get("ShippingAndPackagingUSDOTComment", "")
        if not shipping_desc:
            return ""
        
        # Convert to uppercase for consistent matching
        shipping_desc = shipping_desc.upper()
        
        # Check for non-regulated cases first
        if "NON-REGULATED" in shipping_desc or "NONREGULATED" in shipping_desc:
            return "NON-REGULATED MATERIAL"
            
        if "NONRCRA / NONDOT" in shipping_desc or "NON RCRA / NON DOT" in shipping_desc:
            return "NON RCRA REGULATED, NON DOT REGULATED"
            
        # If not non-regulated, look for UN/NA codes
        pattern = r'(UN\d{4}|NA\d{4})'
        matches = re.findall(pattern, shipping_desc)
        
        return matches[0] if matches else ""

    def _extract_constituents(self, data: Dict[str, Any]) -> str:

        shipping_desc = data.get("ShippingAndPackagingUSDOTComment", "")
        if not shipping_desc:
            return ""
        
        # Pattern to match content within parentheses
        pattern = r'\((.*?)\)'
        matches = re.findall(pattern, shipping_desc)
        
        if matches:
            # Take the first match and clean it up
            constituents = matches[0].strip()
            # Remove any extra spaces around commas
            constituents = ', '.join(part.strip() for part in constituents.split(','))
            return constituents
            
    def _is_rcra_waste(self, data: Dict[str, Any]) -> str:

        # Check the direct hazardous waste indicator
        if data.get("HazardousWaste") == "Yes":
            return "Y"
            
        # Check for any characteristic waste codes (D codes)
        if any(data.get(field) == "Yes" for field in [
            "WCHazardousIgnitable",
            "WCHazardousCorrosive",
            "WCHazardousReactive",
            "WCHazardousToxic"
        ]):
            return "Y"
            
        # Check for listed waste codes (F, K, P, U)
        if any(data.get(field) == "Yes" for field in [
            "WCHazardousF",
            "WCHazardousK",
            "WCHazardousP",
            "WCHazardousU"
        ]):
            return "Y"
            
        # Check if any waste codes are actually listed
        waste_code_fields = [
            "hazardouswastenof",
            "hazardouswastenoK",
            "hazardouswastenoP",
            "hazardouswastenou"
        ]
        
        for field in waste_code_fields:
            if data.get(field) and str(data.get(field)).strip():
                return "Y"
        
        # Check if specifically marked as RCRA exempt
        if data.get("RCRAExempt") == "Yes":
            return "N"
            
        return "N"

    def _extract_rq_info(self, data: Dict[str, Any]) -> str:

        shipping_comment = data.get("ShippingAndPackagingUSDOTComment", "")
        
        # If no shipping comment, return empty
        if not shipping_comment:
            return ""
            
        try:
            # Check if comment starts with RQ
            if shipping_comment.upper().startswith("RQ"):
                # Split by commas and clean up
                parts = [p.strip() for p in shipping_comment.split(",")]
                
                # Look for RQ information
                rq_info = []
                
                for part in parts:
                    part = part.upper()
                    
                    # If it's the RQ marker with substance
                    if part.startswith("RQ"):
                        # Extract just the substance if it's in the same part
                        substance = part.replace("RQ", "").strip()
                        if substance:
                            rq_info.append(substance)
                            
                    # Check for D-codes
                    elif part.startswith("D") and len(part) == 4 and part[1:].isdigit():
                        rq_info.append(part)
                        
                    # Check for chemical names in parentheses
                    elif "(" in part and ")" in part:
                        chemicals = part[part.find("(")+1:part.find(")")].split(",")
                        rq_info.extend([chem.strip() for chem in chemicals])
                
                if rq_info:
                    # Format into required style
                    return f"RQ {', '.join(rq_info)}"
                    
        except Exception:
            # If any parsing error, return empty string
            return ""
        
        return ""

    def _has_dot_special_permit(self, data: Dict[str, Any]) -> str:

        # Fields to check for DOT-SP references
        fields_to_check = [
            "ShippingAndPackagingUSDOTComment",
            "fddDOTNotesSpecialPermits",
            "TransportationRequirement"
        ]
        
        # Patterns that indicate a DOT special permit
        sp_patterns = [
            "DOT-SP",
            "SP-",
            "SPECIAL PERMIT",
            "SP ",  # Space after SP to avoid matching other abbreviations
        ]
        
        # Check each field
        for field in fields_to_check:
            value = str(data.get(field, "")).upper()
            if any(pattern in value for pattern in sp_patterns):
                return "Y"
                
        return "N"

    def _extract_special_permit_number(self, data: Dict[str, Any]) -> str:
        
        # If no special permit indicated, return empty
        if self._has_dot_special_permit(data) == "N":
            return ""
        
        # Fields to check for DOT-SP numbers
        fields_to_check = [
            "ShippingAndPackagingUSDOTComment",
            "fddDOTNotesSpecialPermits",
            "TransportationRequirement"
        ]
        
        # Patterns to match special permit numbers
        patterns = [
            r"DOT-SP[- ]?(\d+)",  # Matches DOT-SP12345 or DOT-SP 12345
            r"SP[- ]?(\d+)",      # Matches SP12345 or SP 12345
            r"SPECIAL PERMIT[- #]?(\d+)"  # Matches SPECIAL PERMIT 12345
        ]
        
        # Check each field
        for field in fields_to_check:
            value = str(data.get(field, "")).upper()
            
            # Try each pattern
            for pattern in patterns:
                match = re.search(pattern, value)
                if match:
                    # Return just the number portion
                    return match.group(1)
                    
        return ""
    
# Example usage:
if __name__ == "__main__":
    # Read sample data
    with open('sample_data\sample_pulled_data.json', 'r', encoding='utf-8') as f:
        sample_data = json.load(f)
        
    # Get profile ID from the data
    profile_id = sample_data.get('Profile_Number', 'unknown')
    
    # Initialize mapper and convert
    mapper = WasteProfileMapper()
    html_elements = mapper.map_profile(sample_data)
    
    # Print results
    print("\nHTML Element Mapping:")
    print(json.dumps(html_elements, indent=2))
    

    save_mappings(html_elements, profile_id)