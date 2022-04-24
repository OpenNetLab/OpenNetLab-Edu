def new_packet(seqno: int, ackno: int, message: str):
    return {
        'seqno': seqno,
        'ackno': ackno,
        'message': message
    }
