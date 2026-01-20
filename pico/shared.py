import _thread


cprint_enabled = False
nprint_enabled = False
delimiter_line = "=========="



nr_of_channels = 26
mux_ch = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12 , # 13, 14, 15,
          0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12   #, 13, 14, 15
            ]

output_adc_ch = [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,# 1, 1, 1
                0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,# 0, 0, 0, 
                ]

output_adc_value = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, # 0, 0, 0, 
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0#, 0, 0, 0
                        ]

output_adc_value_avg = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, # 0, 0, 0, 
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0#, 0, 0, 0
                        ]


output_adc_value_v = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, # 0, 0, 0, 
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 #, 0, 0, 0
                        ]


output_adc_value_min = [1.1, 4.9, 1.4, 3.2, 1., 1., 1., 1., 4.9, 2.4, 1.9, 0.9, 0.8,
                        1.1, 4.9, 1.4, 3.2, 1., 1., 1., 1., 4.9, 2.4, 1.9, 0.9, 0.8
                        ]

output_adc_value_max = [1.3, 5.1, 1.6, 3.4, 5.1, 5.1, 5.1, 5.1, 5.1, 2.6, 1.7, 1.1, 1.,
                        1.1, 4.9, 1.4, 3.2, 1., 1., 1., 1., 4.9, 2.4, 1.9, 0.9, 0.8
                        ]



output_adc_value_min_test = [-0.5, -0.5, -0.5, -0.5, -0.5, -0.5, -0.5, -0.5, -0.5, -0.5, -0.5, -0.5, -0.5,
                        -0.5, -0.5, -0.5, -0.5, -0.5, -0.5, -0.5, -0.5, -0.5, -0.5, -0.5, -0.5, -0.5
                        ]

output_adc_value_max_test = [5.5, 5.5, 5.5, 5.5, 5.5, 5.5, 5.5, 5.5, 5.5, 5.5, 5.5, 5.5, 5.5,
                        5.5, 5.5, 5.5, 5.5, 5.5, 5.5, 5.5, 5.5, 5.5, 5.5, 5.5, 5.5, 5.5
                        ]



adc_resolution = 4096  # 12-bit ADC
adc_reference_voltage = 3.3  # Reference voltage for ADC in volts
adc_cal = adc_reference_voltage / adc_resolution  # Volts per ADC count

db_1v2_cal = 0.8291 # 3300./(680.+3300)
db_5v0_cal = 0.5 # 3300./(3300.+3300)
db_1v5_cal = 0.8291 # 3300./(680.+3300)
db_3v3_cal = 0.5 # 3300./(3300.+3300)
db_pg_cal = 0.5 # 3300./(3300.+3300)
db_5v0pp_cal = 0.5 # 3300./(3300.+3300)
db_2v5_cal = 0.8291 # 3300./(680.+3300)
db_1v8_cal = 0.8291 # 3300./(680.+3300)
db_1v0_cal = 0.8291 # 3300./(680.+3300)
db_0v95_cal = 0.8291 # 3300./(680.+3300)

output_adc_value_v_calibration_factor = [db_1v2_cal, db_5v0_cal, db_1v5_cal, db_3v3_cal, db_pg_cal, db_pg_cal, db_pg_cal, db_pg_cal, db_5v0pp_cal, db_2v5_cal, db_1v8_cal, db_1v0_cal, db_0v95_cal,
                                            db_1v2_cal, db_5v0_cal, db_1v5_cal, db_3v3_cal, db_pg_cal, db_pg_cal, db_pg_cal, db_pg_cal, db_5v0pp_cal, db_2v5_cal, db_1v8_cal, db_1v0_cal, db_0v95_cal]


channel_label = ["dba_1v2", "dba_5v0", "dba_1v5", "dba_3v3", "dba_pg2", "dba_pg3", "dba_pg4", "dba_pg1", "dba_5v0p", "dba_2v5", "dba_1v8", "dba_1v0",  "dba_0v95",
                "dbb_1v2", "dbb_5v0", "dbb_1v5", "dbb_3v3", "dbb_pg2", "dbb_pg3", "dbb_pg4", "dbb_pg1", "dbb_5v0p", "dbb_2v5", "dbb_1v8", "dbb_1v0",  "dbb_0v95"
                ]









data_lock = _thread.allocate_lock()
