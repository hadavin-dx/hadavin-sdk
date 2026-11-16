A = "tests/test_r7u_a_findings.py"; B = "tests/test_r7u_b_findings.py"; C = "tests/test_r7u_c_findings.py"
UNIT_CAP = "test_a1_one_more or test_a1_the_rule or test_a1_named or test_a1b_a_retried"
RD = "test_a2 and not real_run"
NK = "test_a3_a_counter_that_is_not_known"
CONT = "test_a3_contacts_not_accounted"
CK = "test_a3_the_counter_check"
A4_NK = "test_a4_the_readback_note_does_not_name"; A4_SH = "test_a4_the_readback_note_shows"; A4_NO = "test_a4_the_readback_note_with_no_open"; A4_MO = "test_a4_the_readback_note_gives"
ZK = "b8 or c1 or c2 or c3 or c4 or c5 or c6 or c7 or t6 or t12"
K = {
 "X01": ([A, B], RD + " or b7_one_unreadable or b7_a_real_mail"),
 "X02": ([A], NK), "X03": ([A], NK), "X04": ([A], "a1c"), "X05": ([A], "a1c"), "X06": ([A], "a1c"),
 "X07": ([A], A4_SH), "X08": ([A], NK + " or " + CONT), "X09": ([A], CONT),
 "X10": ([A, B], NK + " or b5_a_hidden_contact_and_a_counter"), "X11": ([B], "b7_one_unreadable"),
 "X12": ([B], "b7_one_unreadable or b7_a_real_mail"), "X13": ([B], "b7_the_run_says_in_words"),
 "X14": ([A, B], NK + " or b5_a_hidden"), "X16": ([A], A4_NK), "X17": ([A], A4_NK + " or " + A4_SH),
 "X18": ([A], A4_MO), "X19": ([A], A4_SH), "X20": ([A], CK), "X21": ([B], "b7_the_mail_counter_rule or b7_a_run_with_a_readable"),
 "X22": ([B], "b7_the_mail_counter_rule or b7_a_run_with_a_readable"), "X23": ([B], "b7_one_unreadable or b7_a_real_mail"),
 "X24": ([A, B], "test_a2_a_counter_with_a_bad_value or b5_a_hidden"),
 "Y01": ([A], UNIT_CAP), "Y02": ([A], UNIT_CAP), "Y03": ([A], UNIT_CAP), "Y04": ([A], UNIT_CAP),
 "Y05": ([A], RD), "Y06": ([A, B], RD + " or b7_one_unreadable"), "Y07": ([A], RD), "Y08": ([A], RD), "Y09": ([A], RD + " or b7_a_real_mail"),
 "Y10": ([A], RD), "Y11": ([A], RD), "Y12": ([A], NK), "Y13": ([A], UNIT_CAP + " or " + CONT), "Y14": ([A], NK),
 "Y15": ([A], CONT), "Y16": ([A], NK + " or test_a2_a_counter_with_a_bad_value"), "Y17": ([A], NK), "Y18": ([A], CONT),
 "Y19": ([A], "a1c"), "Y20": ([A], A4_NK), "Y21": ([A], A4_SH + " or " + A4_NO), "Y22": ([A], A4_NK), "Y23": ([A], A4_SH),
 "Y24": ([A], A4_MO), "Y25": ([A], A4_NK), "Y26": ([A], CK), "Y27": ([A], CK), "Y28": ([A], CK), "Y29": ([A], CK),
 "Y30": ([B], "b7_the_run_says_in_words"),
}
for z in range(1, 17): K["Z%02d" % z] = ([C, B, "tests/test_r7t_findings.py"], ZK)
