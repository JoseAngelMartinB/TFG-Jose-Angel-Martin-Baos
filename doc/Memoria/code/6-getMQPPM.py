def getMQPPM(self, rs_ro_ratio, mq_curve):
    """
    Calculate the ppm of the target gas using the slope and a point
    form the line obtained aproximating the sensitivity characteristic curve.


    Input:   rs_ro_ratio -> Value obtained of the division Rs/Ro
             mq_curve -> Line obtained using two points form the sensitivity
                characteristic curve
    Output:  Current gas percentage in the environment
    """
    return (math.pow(10, (math.log10(rs_ro_ratio)-mq_curve[1]) / mq_curve[0]))

