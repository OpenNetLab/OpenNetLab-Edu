def new_packet(absno: int, seqno: int, ackno: int, message: str):
    return {
        'absno': absno,
        'seqno': seqno,
        'ackno': ackno,
        'message': message
    }
