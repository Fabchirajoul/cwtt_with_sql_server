document.addEventListener("alpine:init", () => {
  Alpine.data("CWTTFRAMEWORK", () => {
    return {
      Admin_Home_Page: true,
      Admin_setting: false,
      Admin_full_dislay: false,
      Admin_last_icon: false,
      add_new_user: false,
      update_user_password: false,
      activate_deactivate_user: false,
      update_existing_username: false,
      update_survey_status: false,
      add_gps_location: false,
      add_new_question: false,
      display_all_question_per_survey: false,
      update_question: false,
      update_question_value: false,
      update_question_index: false,
      refresh_all_account_details: false,
      create_new_survey: false,
      update_existing_survey_name: false,
      copy_survey: false,
      update_survey_status: false,
      update_master_survey_survey: false,
      add_gps_location: false,
      refersh_gps_table: false,
      update_gps_table: false,
      display_all_surveys: false,
      add_new_question_option_for_drop_down_or_tick_box: false,
      delete_question_option: false,
      refersh_branching_table_dd_option_for_next_question_index: false,
      copy_question_option_to_tb_or_db: false,
      update_question_option_with_new_value: false,
      display_all_responses_per_question_dd_or_tb: false,
      update_next_question_option_index_dropdown: false,
      add_new_question_options_for_drop_down: false,
      view_submitted_response:false,
      delete_question_option:false,

      openHome(currentSection) {
        this.Admin_Home_Page = true;
        this.Admin_setting = false;
        this.Admin_full_dislay = false;
        this.Admin_last_icon = false;
        this.add_new_user = false;
        this.update_user_password = false;
        this.activate_deactivate_user = false;
        this.update_existing_username = false;
        this.update_survey_status = false;
        this.add_gps_location = false;
        this.add_new_question = false;
        this.display_all_question_per_survey = false;
        this.update_question = false;
        this.update_next_question_index_for_question = false;
        this.update_question_index_with_new_value = false;
        this.refresh_all_account_details = false;
        this.create_new_survey = false;
        this.update_existing_survey_name = false;
        this.copy_survey = false;
        this.update_survey_status_survey = false;
        this.update_master_survey_survey = false;
        this.add_gps_location = false;
        this.refersh_gps_table = false;
        this.update_gps_table = false;
        this.display_all_surveys = false;
        this.add_new_question_options_for_drop_down = false;
        this.view_submitted_response = false;
       

        // Question_option
        this.add_new_question_option_for_drop_down_or_tick_box = false;
        this.delete_question_option = false;
        this.refersh_branching_table_dd_option_for_next_question_index = false;
        this.copy_question_option_to_tb_or_db = false;
        this.update_question_option_with_new_value = false;
        this.display_all_responses_per_question_dd_or_tb = false;
        this.update_next_question_option_index_dropdown = false;

        if (currentSection == "Admin_setting") {
          this.Admin_Home_Page = false;
          this.Admin_setting = true;
        } else if (currentSection == "Admin_full_dislay") {
          this.Admin_Home_Page = false;
          this.Admin_full_dislay = true;
        } else if (currentSection == "Admin_last_icon") {
          this.Admin_Home_Page = false;
          this.Admin_last_icon = true;
        } else if (currentSection == "activate_deactivate_user") {
          this.Admin_Home_Page = false;
          this.activate_deactivate_user = true;
        } else if (currentSection == "add_new_user") {
          this.Admin_Home_Page = false;
          this.add_new_user = true;
        } else if (currentSection == "update_user_password") {
          this.Admin_Home_Page = false;
          this.update_user_password = true;
        } else if (currentSection == "update_existing_username") {
          this.Admin_Home_Page = false;
          this.update_existing_username = true;
        } else if (currentSection == "update_survey_status") {
          this.Admin_Home_Page = false;
          this.update_survey_status = true;
        } else if (currentSection == "add_gps_location") {
          this.Admin_Home_Page = false;
          this.add_gps_location = true;
        } else if (currentSection == "add_new_question") {
          this.Admin_Home_Page = false;
          this.add_new_question = true;
        } else if (currentSection == "display_all_question_per_survey") {
          this.Admin_Home_Page = false;
          this.display_all_question_per_survey = true;
        } else if (currentSection == "update_question") {
          this.Admin_Home_Page = false;
          this.update_question = true;
        } else if (
          currentSection == "update_next_question_index_for_question"
        ) {
          this.Admin_Home_Page = false;
          this.update_next_question_index_for_question = true;
        } else if (currentSection == "update_question_index_with_new_value") {
          this.Admin_Home_Page = false;
          this.update_question_index_with_new_value = true;
        } else if (currentSection == "refresh_all_account_details") {
          this.Admin_Home_Page = false;
          this.refresh_all_account_details = true;
        } else if (currentSection == "create_new_survey") {
          this.Admin_Home_Page = false;
          this.create_new_survey = true;
        } else if (currentSection == "update_existing_survey_name") {
          this.Admin_Home_Page = false;
          this.update_existing_survey_name = true;
        } else if (currentSection == "copy_survey") {
          this.Admin_Home_Page = false;
          this.copy_survey = true;
        } else if (currentSection == "update_survey_status_survey") {
          this.Admin_Home_Page = false;
          this.update_survey_status_survey = true;
        } else if (currentSection == "update_master_survey_survey") {
          this.Admin_Home_Page = false;
          this.update_master_survey_survey = true;
        } else if (currentSection == "add_gps_location") {
          this.Admin_Home_Page = false;
          this.add_gps_locatio = true;
        } else if (currentSection == "refersh_gps_table") {
          this.Admin_Home_Page = false;
          this.refersh_gps_table = true;
        } else if (currentSection == "update_gps_table") {
          this.Admin_Home_Page = false;
          this.update_gps_table = true;
        } else if (currentSection == "display_all_surveys") {
          this.Admin_Home_Page = false;
          this.display_all_surveys = true;
        } else if (currentSection == "add_new_question_options_for_drop_down") {
          this.Admin_Home_Page = false;
          this.add_new_question_options_for_drop_down = true;
        } else if (currentSection == "view_submitted_response") {
          this.Admin_Home_Page = false;
          this.view_submitted_response = true;
        }else if (currentSection == "delete_question_option") {
          this.Admin_Home_Page = false;
          this.delete_question_option = true;
        }


        else if (currentSection == "refersh_branching_table_dd_option_for_next_question_index") {
          this.Admin_Home_Page = false;
          this.refersh_branching_table_dd_option_for_next_question_index = true;
        }else if (currentSection == "copy_question_option_to_tb_or_db") {
          this.Admin_Home_Page = false;
          this.copy_question_option_to_tb_or_db = true;
        }else if (currentSection == "update_question_option_with_new_value") {
          this.Admin_Home_Page = false;
          this.update_question_option_with_new_value = true;
        }else if (currentSection == "display_all_responses_per_question_dd_or_tb") {
          this.Admin_Home_Page = false;
          this.display_all_responses_per_question_dd_or_tb = true;
        }else if (currentSection == "update_next_question_option_index_dropdown") {
          this.Admin_Home_Page = false;
          this.update_next_question_option_index_dropdown = true;
        }
      },

      init() {},
    };
  });
});
