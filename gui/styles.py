def configure_styles(style):
    LIGHT_PINK = '#FFB6C1'
    LIGHT_BLUE = '#87CEFA'
    LIGHT_GREEN = '#90EE90'
    LAVENDER = '#E6E6FA'

    style.theme_use('clam')
    style.configure('Primary.TButton',
                    background=LIGHT_GREEN,
                    foreground='black',
                    font=('Helvetica', 10, 'bold'),
                    padding=8)
    style.configure('Secondary.TButton',
                    background=LIGHT_BLUE,
                    foreground='black',
                    font=('Helvetica', 10, 'bold'),
                    padding=8)
    style.configure('Danger.TButton',
                    background=LIGHT_PINK,
                    foreground='black',
                    font=('Helvetica', 10, 'bold'),
                    padding=8)
    style.configure('Custom.Horizontal.TProgressbar',
                    background=LIGHT_GREEN,
                    troughcolor=LAVENDER)
    style.configure('Main.TFrame', background=LAVENDER)
