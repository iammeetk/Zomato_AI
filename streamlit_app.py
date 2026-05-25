import streamlit as st
from restaurant_rec.phase4.service import RecommendationService
from restaurant_rec.phase2.preferences import PreferenceDTO

st.set_page_config(page_title="Zomato AI Backend API", page_icon="🍔")

@st.cache_resource
def get_service():
    service = RecommendationService()
    try:
        service.load()
    except Exception as e:
        st.error(f"Failed to load dataset. Make sure to run `python -m restaurant_rec ingest` first if testing locally. Error: {e}")
    return service

st.title("Zomato AI - Streamlit Backend")
st.write("This Streamlit app provides an interface for the Zomato AI recommendation engine backend.")

service = get_service()

if service.is_loaded:
    st.success("Backend dataset loaded successfully.")
    
    with st.form("test_api"):
        st.subheader("Test Recommendation API")
        locality = st.text_input("Locality", "Delhi")
        budget = st.selectbox("Budget", ["low", "medium", "high"], index=1)
        cuisine = st.text_input("Cuisines (comma separated)", "North Indian")
        min_rating = st.slider("Min Rating", 1.0, 5.0, 4.0, 0.1)
        additional = st.text_input("Additional Preferences", "family friendly")
        
        submitted = st.form_submit_button("Get Recommendations")
        
        if submitted:
            cuisine_list = [c.strip() for c in cuisine.split(",") if c.strip()]
            prefs = PreferenceDTO(
                locality=locality,
                budget=budget,
                cuisine=cuisine_list,
                min_rating=min_rating,
                additional_preferences=additional if additional else None
            )
            
            with st.spinner("Fetching recommendations from LLM..."):
                try:
                    resp = service.recommend(prefs)
                    if resp.message:
                        st.warning(resp.message)
                    else:
                        st.write(f"Returned {resp.returned_count} candidates out of {resp.filter_count} filtered.")
                        for item in resp.items:
                            with st.expander(f"{item.name} - {item.rating}⭐ - {item.estimated_cost}"):
                                st.write(f"**Cuisine:** {item.cuisine}")
                                st.write(item.explanation)
                except Exception as e:
                    st.error(f"Error during recommendation: {e}")
else:
    st.warning("Service is not loaded. Please ensure dataset is ingested.")
