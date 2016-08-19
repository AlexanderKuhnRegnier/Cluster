def hexify(frame,columns=['Reset Count','Packet Start HF','Previous Sun Pulse',
                          'Most Recent Sun Pulse','First 1ry HF',
                          'First 2ry HF'],inplace=False):
    '''
    Converts selected columns to an upper case hex format
    '''
    if not inplace:
        frame = frame.copy()
    hex_format = lambda i:'{:x}'.format(i).upper()
    for column in columns:
        frame[column]=frame[column].apply(hex_format)
    if inplace:
        return None
    else:
        return frame