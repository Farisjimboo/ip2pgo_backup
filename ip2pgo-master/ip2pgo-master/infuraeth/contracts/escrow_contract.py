from django.conf import settings

contract = """
pragma solidity ^0.4.24;

contract Escrow {
    address public admin;
    uint public amount;
    string public fiat;
    address public taker;    
    bool public released;
    bool public cancelled;
    bool public trading;

    constructor (address _taker, uint _amount, string _fiat) public {
        admin = msg.sender;
        taker = _taker;
        amount = _amount;
        fiat = _fiat;
        trading = true;
    }
    
    modifier adminOnly {
        require(msg.sender == admin);
        _;
    }
    
    function release () adminOnly public {
        require(cancelled == false);
        released = true;
        trading = false;
    }

    function cancel () adminOnly public {
        require(released == false);
        cancelled = true;
        trading = false;
    }
}
"""
name = "Escrow"
