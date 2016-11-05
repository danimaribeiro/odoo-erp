
result = D(0)

if 'SAL_13' in locals():
    result += SAL_13

if 'SAL_13_AP' in locals():
    result += SAL_13_AP

if 'DESC_1A_PARC_13' in locals():
    result -= DESC_1A_PARC_13

if 'DESC_2A_PARC_13' in locals():
    result -= DESC_2A_PARC_13

if 'BASE_INSS_13_RESCISAO_ORIGINAL' in locals():
    result -= BASE_INSS_13_RESCISAO_ORIGINAL

if result < 0:
    result = 0
