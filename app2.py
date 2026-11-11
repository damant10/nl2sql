import os
import pandas as pd
import streamlit as st
from dataconnecttion import getResults
from hashCheck import get_df_hash_order_independent
from nlp2sql import NLPtoSQl

st.title("Excel File Upload")

##use of os module for handling file systems like excel
output_dir = "./output"
os.makedirs(output_dir, exist_ok=True)

uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx", "xls"])

if uploaded_file is not None:
    try:
        # Load and display initial data preview
        df = pd.read_excel(uploaded_file)
        st.write("Data Preview:")
        st.dataframe(df)

##type="primary" means good colour not lighter ones
        # Trigger processing on button click
        if st.button("Run Accuracy Evaluation", type="primary"):
            NL = df[["NL query"]].values.tolist()      ##english query list created
            CorrectSQL = df[["Correct SQL"]].values.tolist()    ## correct sql list created
            dfAccuracy = []  ## new list for storing accuracy created

            with st.spinner("Processing queries and evaluating accuracy..."): ##keep showing this msg till line 64 is executed
                for i in range(len(NL)):
                    nl_query = NL[i][0]
                    actual_sql = CorrectSQL[i][0]

                    sqlQuery = NLPtoSQl(nl_query)  ## convert eng query to sql
                    dfGenerated = getResults(sqlQuery)  ##run the nl2sql query
                    dfActual = getResults(actual_sql)  ##run correct sql

                    # if dfGenerated i.e. nl2sql query results is a dataframe then store it in .csv format in 'output' folder else if results returned is NULL then no need to store
                    if isinstance(dfGenerated, pd.DataFrame):
                        dfGenerated.to_csv(
                            os.path.join(output_dir, f"dfGenerated_{i}.csv"),
                            index=False,
                        )

                     ## if dfActual i.e. correct sql query results is a dataframe then store it in .csv format in 'output' folder else if results returned is NULL then no need to store   
                    if isinstance(dfActual, pd.DataFrame):
                        dfActual.to_csv(
                            os.path.join(output_dir, f"dfActual_{i}.csv"),
                            index=False,
                        )

                    # Compare generated vs actual dataframes
                    #compare only if dataframe results have been generated
                    if isinstance(dfGenerated, pd.DataFrame) and isinstance(dfActual, pd.DataFrame):
                        is_equal = (
                            get_df_hash_order_independent(dfGenerated)
                            == get_df_hash_order_independent(dfActual)

                        )
                    else:
                        is_equal = False

                    if is_equal:
                        dfAccuracy.append("Yes")
                    else:
                        dfAccuracy.append("No")

            # Store computed results in session_state so they persist
            df["Matching"] = dfAccuracy
            st.session_state["processed_df"] = df
            st.session_state["num_rows"] = len(NL)

        # Display results and downloadable CSV links if processing is completed
        if "processed_df" in st.session_state:
            st.success("Evaluation complete!")
            st.write("Results Preview:")
            st.dataframe(st.session_state["processed_df"])

            st.divider()
            st.subheader("Generated CSV Files")

            # Loop through each row and render download buttons
            for i in range(st.session_state["num_rows"]):
                gen_file = os.path.join(output_dir, f"dfGenerated_{i}.csv") ##genfile will handle path of ith eng query output
                act_file = os.path.join(output_dir, f"dfActual_{i}.csv")  ##actfile will handle path of ith actual sql query output

                ##it will decide font size
                st.markdown(f"### Files for row no. {i+1}")
                
                ##divides the page into 2 cols for Ebg query and correct sql csv output download
                col1, col2 = st.columns(2)

                # Download button for dfGenerated_i i.e. english query results
                with col1:
                    st.write(f"**English_Query_{i+1}**")
                    if os.path.exists(gen_file):
                        with open(gen_file, "rb") as f:
                            st.download_button(
                                label=f"Download English_Query_{i+1}",
                                data=f.read(),  ##read contents of file from path gen_file
                                file_name=f"dfGenerated_{i}.csv", ## when we click the button with which name it will get generated
                                mime="text/csv",
                                key=f"btn_gen_{i}",
                            )
                    else:
                        st.warning("File not found") ## if file does not exist show error msg

                # Download button for dfActual_i i.e. actual sql results
                ##Same procedure as above
                with col2:
                    st.write(f"**Correct_SQL_{i+1}**")
                    if os.path.exists(act_file):
                        with open(act_file, "rb") as f:
                            st.download_button(
                                label=f"Download Correct_SQL_{i+1}",
                                data=f.read(),
                                file_name=f"dfActual_{i}.csv",
                                mime="text/csv",
                                key=f"btn_act_{i}",
                            )
                    else:
                        st.warning("File not found")

                st.divider()

    except Exception as e:
        st.error(f"Error processing file: {e}")