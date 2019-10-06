from seq_script import extract_seq, convert_pam

guide = []
guide.extend(convert_pam.getGuides('AACAGCGACAGAGAGGCATCAGAGGCCAGGG', 'NGG', 20))
print(guide)
print('\n'.join(guide).strip())